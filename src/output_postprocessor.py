from __future__ import annotations

import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import webvtt

from config.settings import AppSettings, local_storage_paths
from src.storage.base import StorageFile, StorageProvider
from src.vtt_builder import VTTBuilder

logger = logging.getLogger(__name__)
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".wmv", ".avi", ".webm"}
TIMESTAMP_EPSILON = 0.001


class OutputPostProcessor:
    """Recover subtitle artefacts and optionally generate TTS for existing outputs."""

    def __init__(self, settings: AppSettings, storage: StorageProvider) -> None:
        self.settings = settings
        self.storage = storage

    def process_target(self, target: str) -> dict[str, Any]:
        folders = [item for item in self.storage.list_children(target) if item.is_directory and item.name != "_manifests"]
        results = []
        for folder in sorted(folders, key=lambda item: item.name.lower()):
            try:
                results.append(self.process_folder(folder.id))
            except Exception as exc:
                logger.exception("Output recovery failed for %s", folder.name)
                results.append({"folder": folder.name, "status": "error", "error_type": type(exc).__name__, "error": str(exc)})
        failures = sum(item.get("status") == "error" for item in results)
        return {
            "status": "partial" if failures else "success",
            "folders": len(results),
            "failed": failures,
            "vtt_repaired": sum(bool(item.get("vtt_repaired")) for item in results),
            "tts_generated": sum(bool(item.get("tts_generated")) for item in results),
            "tts_skipped": sum(bool(item.get("tts_skipped")) for item in results),
            "results": results,
        }

    def process_folder(self, folder: str) -> dict[str, Any]:
        files = [item for item in self.storage.list_children(folder) if not item.is_directory]
        video = self._preferred_video(files)
        translated = self._pick_vtt(files, f"_{self.settings.target_lang.lower()}")
        original_folder = next((item for item in self.storage.list_children(folder) if item.is_directory and item.name == self.settings.original_transcript_subdir), None)
        original = self._pick_vtt(self.storage.list_children(original_folder.id), "_original") if original_folder else None
        result = {"folder": Path(folder).name, "status": "success", "video": video.name if video else None, "translated_vtt": translated.name if translated else None, "original_vtt": original.name if original else None, "vtt_repaired": False, "repair_actions": [], "tts_generated": False, "tts_skipped": False}
        if video is None:
            result.update({"status": "skipped", "reason": "No source video found in output folder"})
            return result

        work = local_storage_paths()["work"]
        work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="output-recovery-", dir=work) as tmp:
            root = Path(tmp)
            video_local = self._download(video, root / video.name)
            original_segments = self._read_vtt(original, root, "original")
            translated_segments = self._read_vtt(translated, root, "translated")
            original_was_invalid = original is not None and original_segments is None

            if original_segments is None:
                from src.stt_engine import STTEngine
                original_segments = STTEngine(self.settings).transcribe(video_local)
                self._assert_valid(original_segments, "recovered STT")
                new_original = root / (original.name if original else f"{video_local.stem}_original.vtt")
                VTTBuilder.generate_vtt(original_segments, new_original)
                self._replace_vtt(original, original_folder.id if original_folder else self.storage.ensure_folder(folder, self.settings.original_transcript_subdir), new_original)
                result["vtt_repaired"] = True
                result["repair_actions"].append("stt")

            if translated_segments is None or original_was_invalid:
                from src.translator import TextTranslator
                translated_segments = TextTranslator(self.settings).translate_segments(original_segments)
                self._assert_valid(translated_segments, "recovered translation")
                new_translated = root / (translated.name if translated else f"{video_local.stem}_{self.settings.target_lang.lower()}.vtt")
                VTTBuilder.generate_vtt(translated_segments, new_translated)
                self._replace_vtt(translated, folder, new_translated)
                result["vtt_repaired"] = True
                result["repair_actions"].append("translation")

            if self.settings.tts_enabled:
                tts_mp4_name = f"{video_local.stem}_tts.mp4"
                if self.storage.file_exists(folder, tts_mp4_name) and not result["vtt_repaired"]:
                    result["tts_skipped"] = True
                else:
                    translated_local = root / "translated.vtt"
                    VTTBuilder.generate_vtt(translated_segments, translated_local)
                    webm = self._preferred_webm(files)
                    webm_local = self._download(webm, root / webm.name) if webm else None
                    from src.tts_pipeline import generate_tts_media
                    tts = generate_tts_media(video_local, translated_local, root, video_local.stem, self.settings, webm_video_path=webm_local)
                    self.storage.upload_file(tts.audio_path, folder, "audio/wav")
                    self.storage.upload_file(tts.mp4_path, folder, "video/mp4")
                    if tts.webm_path:
                        self.storage.upload_file(tts.webm_path, folder, "video/webm")
                    result.update({"tts_generated": True, "tts_audio": tts.audio_path.name, "tts_mp4": tts.mp4_path.name, "tts_webm": tts.webm_path.name if tts.webm_path else None, "tts_cues": tts.cue_count, "tts_adjusted_cues": tts.adjusted_cues})
        return result

    @staticmethod
    def _preferred_video(files: list[StorageFile]) -> StorageFile | None:
        usable = [item for item in files if Path(item.name).suffix.lower() in VIDEO_EXTENSIONS and "_tts" not in Path(item.name).stem.lower()]
        mp4 = [item for item in usable if Path(item.name).suffix.lower() == ".mp4"]
        return sorted(mp4 or usable, key=lambda item: item.name.lower())[0] if usable else None

    @staticmethod
    def _preferred_webm(files: list[StorageFile]) -> StorageFile | None:
        usable = [item for item in files if Path(item.name).suffix.lower() == ".webm" and "_tts" not in Path(item.name).stem.lower()]
        return sorted(usable, key=lambda item: item.name.lower())[0] if usable else None

    @staticmethod
    def _pick_vtt(files: list[StorageFile], preferred_contains: str) -> StorageFile | None:
        vtts = [item for item in files if Path(item.name).suffix.lower() == ".vtt" and ".bak." not in item.name.lower()]
        preferred = [item for item in vtts if preferred_contains.lower() in item.name.lower()]
        return sorted(preferred or vtts, key=lambda item: item.name.lower())[0] if vtts else None

    def _download(self, remote: StorageFile, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.storage.download_file(remote, destination)
        return destination

    def _read_vtt(self, remote: StorageFile | None, root: Path, label: str) -> list[dict[str, Any]] | None:
        if remote is None:
            return None
        path = root / f"{label}.vtt"
        try:
            self.storage.download_file(remote, path)
            captions = webvtt.read(str(path))
            segments = [{"start": c.start_in_seconds, "end": c.end_in_seconds, "text": c.text.strip()} for c in captions]
        except Exception as exc:
            logger.warning("Cannot parse %s VTT %s: %s", label, remote.name, exc)
            return None
        return segments if self._valid_segments(segments) else None

    @staticmethod
    def _valid_segments(segments: list[dict[str, Any]]) -> bool:
        if not segments:
            return False
        previous_end = -1.0
        for segment in segments:
            try:
                start, end = float(segment["start"]), float(segment["end"])
            except (KeyError, TypeError, ValueError):
                return False
            if start < 0 or end <= start or start + TIMESTAMP_EPSILON < previous_end:
                return False
            previous_end = end
        return True

    def _assert_valid(self, segments: list[dict[str, Any]], label: str) -> None:
        if not self._valid_segments(segments):
            raise ValueError(f"{label} contains invalid subtitle timing")

    def _replace_vtt(self, current: StorageFile | None, parent: str, replacement: Path) -> None:
        target_name = current.name if current else replacement.name
        if current:
            old = self._download(current, replacement.parent / f"old-{current.name}")
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
            backup_name = f"{current.name}.bak.{stamp}"
            while self.storage.file_exists(parent, backup_name):
                stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
                backup_name = f"{current.name}.bak.{stamp}"
            backup = replacement.parent / backup_name
            backup.write_bytes(old.read_bytes())
            self.storage.upload_file(backup, parent, "text/vtt")
        named = replacement.parent / target_name
        named.write_bytes(replacement.read_bytes())
        self.storage.upload_file(named, parent, "text/vtt")
