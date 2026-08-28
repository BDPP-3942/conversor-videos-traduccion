from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

import webvtt

from config.settings import AppSettings, local_storage_paths, resolve_project_path
from src.storage.base import StorageFile, StorageProvider
from src.vtt_builder import VTTBuilder

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".wmv", ".avi", ".webm"}
TIMESTAMP_EPSILON = 0.001


class OutputPostProcessor:
    """Repair existing subtitle artefacts and generate optional TTS media.

    The processor is deliberately independent from ZIP ingestion so the same
    recovery path works for fresh runs and already processed output folders.
    """

    def __init__(self, settings: AppSettings, storage: StorageProvider) -> None:
        self.settings = settings
        self.storage = storage

    def process_target(self, target: str) -> dict[str, Any]:
        folders = self._list_output_folders(target)
        results: list[dict[str, Any]] = []
        for folder in folders:
            try:
                result = self.process_folder(folder)
            except Exception as exc:
                logger.exception("Output post-processing failed for %s", folder)
                result = {
                    "folder": folder,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            results.append(result)

        failures = sum(item.get("status") == "error" for item in results)
        repaired = sum(item.get("vtt_repaired") for item in results)
        tts_generated = sum(item.get("tts_generated") for item in results)
        return {
            "status": "partial" if failures else "success",
            "folders": len(results),
            "failed": failures,
            "vtt_repaired": repaired,
            "tts_generated": tts_generated,
            "results": results,
        }

    def process_folder(self, folder: str) -> dict[str, Any]:
        items = [item for item in self.storage.list_children(folder) if not item.is_directory]
        videos = [item for item in items if Path(item.name).suffix.lower() in VIDEO_EXTENSIONS]
        video = self._preferred_video(videos)
        translated = self._find_translated_vtt(items)
        original_folder = next(
            (
                item
                for item in self.storage.list_children(folder)
                if item.is_directory and item.name == self.settings.original_transcript_subdir
            ),
            None,
        )
        original_files = (
            [item for item in self.storage.list_children(original_folder.id) if not item.is_directory]
            if original_folder
            else []
        )
        original = next(
            (item for item in original_files if Path(item.name).suffix.lower() == ".vtt" and ".bak." not in item.name),
            None,
        )

        result: dict[str, Any] = {
            "folder": folder,
            "status": "success",
            "video": video.name if video else None,
            "translated_vtt": translated.name if translated else None,
            "original_vtt": original.name if original else None,
            "vtt_repaired": False,
            "repair_source": None,
            "tts_generated": False,
        }
        if not video and not translated and not original:
            result["status"] = "skipped"
            result["reason"] = "No video or subtitle artefacts found"
            return result

        with tempfile.TemporaryDirectory(prefix="output-repair-", dir=local_storage_paths()["work"]) as tmp:
            root = Path(tmp)
            video_local = self._download(video, root / "video.mp4") if video else None
            original_segments = self._read_valid_vtt(original, "original") if original else None
            translated_segments = self._read_valid_vtt(translated, "translated") if translated else None

            if original_segments is None and video_local is not None:
                original_segments = self._regenerate_stt(video_local)
                self._write_and_replace_vtt(
                    original,
                    original_folder.id if original_folder else self.storage.ensure_folder(folder, self.settings.original_transcript_subdir),
                    original_segments,
                    fallback_name=f"{video_local.stem}_original.vtt",
                )
                result["vtt_repaired"] = True
                result["repair_source"] = "stt"

            if original_segments is not None and translated_segments is None:
                translated_segments = self._translate(original_segments)
                self._write_and_replace_vtt(
                    translated,
                    folder,
                    translated_segments,
                    fallback_name=f"{video_local.stem}_{self.settings.target_lang.lower()}.vtt"
                    if video_local
                    else None,
                )
                result["vtt_repaired"] = True
                result["repair_source"] = "translation"

            if self.settings.tts_enabled:
                if video_local is None or translated_segments is None:
                    raise ValueError("TTS requires a valid video and translated VTT")
                translated_local = root / "translated.vtt"
                VTTBuilder.generate_vtt(translated_segments, translated_local)
                secondary = self._preferred_webm(videos)
                secondary_local = self._download(secondary, root / "video.webm") if secondary else None
                from src.tts_pipeline import generate_tts_media

                tts = generate_tts_media(
                    video_local,
                    translated_local,
                    root,
                    video_local.stem,
                    self.settings,
                    webm_video_path=secondary_local,
                )
                self._upload_if_changed(tts.audio_path, folder, "audio/wav")
                self._upload_if_changed(tts.mp4_path, folder, "video/mp4")
                if tts.webm_path:
                    self._upload_if_changed(tts.webm_path, folder, "video/webm")
                result.update(
                    {
                        "tts_generated": True,
                        "tts_mp4": tts.mp4_path.name,
                        "tts_webm": tts.webm_path.name if tts.webm_path else None,
                        "tts_audio": tts.audio_path.name,
                        "tts_cues": tts.cue_count,
                        "tts_adjusted_cues": tts.adjusted_cues,
                    }
                )

        return result

    def _list_output_folders(self, target: str) -> list[str]:
        return sorted(
            [
                item.id
                for item in self.storage.list_children(target)
                if item.is_directory and item.name != "_manifests"
            ],
            key=str.lower,
        )

    @staticmethod
    def _preferred_video(videos: list[StorageFile]) -> StorageFile | None:
        if not videos:
            return None
        mp4 = [item for item in videos if Path(item.name).suffix.lower() == ".mp4" and "_tts" not in Path(item.name).stem.lower()]
        normal = [item for item in videos if "_tts" not in Path(item.name).stem.lower()]
        return sorted(mp4 or normal or videos, key=lambda item: item.name.lower())[0]

    @staticmethod
    def _preferred_webm(videos: list[StorageFile]) -> StorageFile | None:
        normal = [item for item in videos if Path(item.name).suffix.lower() == ".webm" and "_tts" not in Path(item.name).stem.lower()]
        return sorted(normal, key=lambda item: item.name.lower())[0] if normal else None

    def _find_translated_vtt(self, items: list[StorageFile]) -> StorageFile | None:
        candidates = [
            item
            for item in items
            if Path(item.name).suffix.lower() == ".vtt"
            and "_original" not in item.name.lower()
            and ".bak." not in item.name.lower()
        ]
        if not candidates:
            return None
        preferred = [item for item in candidates if f"_{self.settings.target_lang.lower()}" in item.name.lower()]
        return sorted(preferred or candidates, key=lambda item: item.name.lower())[0]

    def _download(self, remote: StorageFile, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.storage.download_file(remote, destination)
        return destination

    def _read_valid_vtt(self, remote: StorageFile | None, label: str) -> list[dict[str, Any]] | None:
        if remote is None:
            return None
        with tempfile.TemporaryDirectory(prefix="vtt-check-", dir=local_storage_paths()["work"]) as tmp:
            local = Path(tmp) / remote.name
            self.storage.download_file(remote, local)
            try:
                captions = webvtt.read(str(local))
                segments = [
                    {
                        "start": caption.start_in_seconds,
                        "end": caption.end_in_seconds,
                        "text": caption.text.strip(),
                    }
                    for caption in captions
                ]
            except Exception as exc:
                logger.warning("Unable to parse %s VTT %s: %s", label, remote.name, exc)
                return None
        if not self._valid_segments(segments):
            logger.warning("Invalid %s VTT detected: %s", label, remote.name)
            return None
        return segments

    @staticmethod
    def _valid_segments(segments: list[dict[str, Any]]) -> bool:
        if not segments:
            return False
        previous_end = -1.0
        for segment in segments:
            try:
                start = float(segment["start"])
                end = float(segment["end"])
            except (KeyError, TypeError, ValueError):
                return False
            if start < 0 or end <= start:
                return False
            if start + TIMESTAMP_EPSILON < previous_end:
                return False
            previous_end = end
        return True

    def _regenerate_stt(self, video: Path) -> list[dict[str, Any]]:
        from src.stt_engine import STTEngine

        segments = STTEngine(self.settings).transcribe(video)
        if not self._valid_segments(segments):
            raise ValueError(f"STT generated invalid timestamps for {video.name}")
        return segments

    def _translate(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        from src.translator import TextTranslator

        translated = TextTranslator(self.settings).translate_segments(segments)
        if not self._valid_segments(translated):
            raise ValueError("Translation generated invalid timestamps")
        return translated

    def _write_and_replace_vtt(
        self,
        current: StorageFile | None,
        parent: str,
        segments: list[dict[str, Any]],
        *,
        fallback_name: str | None,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="vtt-repair-", dir=local_storage_paths()["work"]) as tmp:
            root = Path(tmp)
            filename = current.name if current else fallback_name
            if not filename:
                raise ValueError("Cannot determine VTT output filename")
            replacement = root / filename
            VTTBuilder.generate_vtt(segments, replacement)
            if current:
                backup = root / f"{filename}.bak.repair"
                backup.write_bytes(self._download(current, root / f"old-{filename}").read_bytes())
                self.storage.upload_file(backup, parent, "text/vtt")
            self.storage.upload_file(replacement, parent, "text/vtt")

    def _upload_if_changed(self, local: Path, parent: str, mime: str) -> None:
        self.storage.upload_file(local, parent, mime)
