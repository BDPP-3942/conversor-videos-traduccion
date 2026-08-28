from __future__ import annotations

import json
import logging
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import webvtt

from config.settings import AppSettings
from src.storage.base import StorageFile, StorageProvider
from src.vtt_builder import VTTBuilder

logger = logging.getLogger(__name__)
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".wmv", ".avi", ".webm"}
TIMESTAMP_EPSILON = 0.001


class SubtitleReprocessor:
    """Repair/rebuild STT and translation VTTs without regenerating the video."""

    def __init__(self, settings: AppSettings, storage: StorageProvider) -> None:
        self.settings = settings
        self.storage = storage
        self._temp_root: Path | None = None
        self._history_name = "reprocess_history"

    def reprocess(
        self,
        target: str,
        *,
        mode: str,
        output_folder: str | None = None,
        video_name: str | None = None,
        source: str | None = None,
        stt_engine_factory: Callable[[], Any] | None = None,
        translator_factory: Callable[[], Any] | None = None,
    ) -> dict[str, Any]:
        mode = mode.lower().replace("-", "_")
        if mode not in {"stt_only", "translate_only", "full"}:
            raise ValueError(f"Unsupported reprocess mode: {mode}")
        if not any((output_folder, video_name, source)):
            raise ValueError("A concrete reprocess target is required; use reprocess_all() for the general case")

        self._temp_root = Path(tempfile.mkdtemp(prefix="subtitle-reprocess-"))
        try:
            folder = self._resolve_output_folder(target, output_folder, video_name, source)
            files = [item for item in self.storage.list_children(folder) if not item.is_directory]
            video = self._resolve_video(files, video_name)
            original_subdir = self.storage.ensure_folder(folder, self.settings.original_transcript_subdir)
            original_files = [item for item in self.storage.list_children(original_subdir) if not item.is_directory]
            original_vtt = self._pick_vtt(original_files, "_original")
            translated_vtt = self._pick_vtt(files, f"_{self.settings.target_lang.lower()}")

            if video is None:
                raise FileNotFoundError(f"No reusable video found in output folder: {folder}")

            original_segments, original_diagnostics = self._try_read_vtt(original_vtt, "existing transcription")
            translated_segments, translated_diagnostics = self._try_read_vtt(translated_vtt, "existing translation")
            repair_original = mode in {"stt_only", "full"} or (mode == "translate_only" and original_segments is None)

            if repair_original:
                video_local = self._download(video, "source.mp4")
                engine = stt_engine_factory() if stt_engine_factory else self._default_stt_engine()
                original_segments = engine.transcribe(video_local)
                self._assert_valid(original_segments, "new STT output")
                new_original = self._write_temp_vtt(original_segments, "original.vtt")
                backup_original = self._backup_and_replace(
                    original_vtt, original_subdir, new_original, fallback_name=self._default_original_name(video.name)
                )
            else:
                backup_original = None

            translation_required = mode in {"translate_only", "full"} or translated_segments is None
            if translation_required:
                if original_segments is None:
                    raise ValueError("Cannot translate without a valid original transcription")
                translator = translator_factory() if translator_factory else self._default_translator()
                translated_segments, translation_failed = self._translate(original_segments, translator)
                self._assert_valid(translated_segments, "new translated VTT")
                new_translated = self._write_temp_vtt(translated_segments, "translated.vtt")
                backup_translated = self._backup_and_replace(
                    translated_vtt,
                    folder,
                    new_translated,
                    fallback_name=f"{Path(video.name).stem}_{self.settings.target_lang.lower()}.vtt",
                )
            else:
                translation_failed = 0
                backup_translated = None

            repaired = bool(backup_original or backup_translated or original_segments is None or translated_segments is None)
            result = {
                "operation": "reprocess_subtitles",
                "mode": mode,
                "status": "partial_translation" if translation_failed else "success",
                "output_folder": folder,
                "video": video.name,
                "previous_transcription": original_vtt.name if original_vtt else None,
                "new_transcription": self._default_original_name(video.name) if repair_original else None,
                "backup_transcription": backup_original,
                "translated_vtt": translated_vtt.name if translated_vtt else f"{Path(video.name).stem}_{self.settings.target_lang.lower()}.vtt",
                "backup_translated_vtt": backup_translated,
                "segments": len(original_segments or []),
                "translation_failed_segments": translation_failed,
                "timestamp_diagnostics_before": {
                    "original": original_diagnostics,
                    "translated": translated_diagnostics,
                },
                "timestamp_repaired": repaired,
                "whisper": {
                    "model": self.settings.whisper_model,
                    "beam_size": self.settings.whisper_beam_size,
                    "vad_filter": self.settings.whisper_vad_filter,
                    "condition_on_previous_text": self.settings.whisper_condition_on_previous_text,
                },
                "translation_preserves_timing": True,
                "ffmpeg_regenerated": False,
            }
            self._write_history(folder, result)
            return result
        finally:
            if self._temp_root:
                import shutil
                shutil.rmtree(self._temp_root, ignore_errors=True)
                self._temp_root = None

    def reprocess_all(self, target: str, *, mode: str, stt_engine_factory=None, translator_factory=None) -> dict[str, Any]:
        mode = mode.lower().replace("-", "_")
        if mode not in {"stt_only", "translate_only", "full"}:
            raise ValueError(f"Unsupported reprocess mode: {mode}")
        folders = self._list_reprocessable_folders(target)
        results = []
        failures = 0
        partial = 0
        for folder in folders:
            try:
                item = self.reprocess(target, mode=mode, output_folder=folder, stt_engine_factory=stt_engine_factory, translator_factory=translator_factory)
                if item.get("status") == "partial_translation":
                    partial += 1
            except Exception as exc:
                failures += 1
                logger.exception("Reprocess failed for output folder %s", folder)
                item = {"operation": "reprocess_subtitles", "mode": mode, "status": "error", "output_folder": folder, "error_type": type(exc).__name__, "error": str(exc)}
            results.append(item)
        status = "error" if failures and not results else "partial_failure" if failures else "partial_translation" if partial else "success"
        return {"operation": "reprocess_subtitles", "scope": "all", "mode": mode, "status": status, "total_candidates": len(folders), "processed": len(folders) - failures, "failed": failures, "partial_translation": partial, "results": results}

    def _list_reprocessable_folders(self, target: str) -> list[str]:
        folders = []
        for child in self.storage.list_children(target):
            if not child.is_directory or child.name == "_manifests":
                continue
            items = self.storage.list_children(child.id)
            if any(not item.is_directory and Path(item.name).suffix.lower() in VIDEO_EXTENSIONS for item in items):
                folders.append(child.name)
                continue
            original = next((item for item in items if item.is_directory and item.name == self.settings.original_transcript_subdir), None)
            if original and any(Path(item.name).suffix.lower() == ".vtt" and ".bak" not in item.name.lower() for item in self.storage.list_children(original.id)):
                folders.append(child.name)
        return sorted(set(folders), key=str.lower)

    def _resolve_output_folder(self, target: str, output_folder: str | None, video_name: str | None, source: str | None) -> str:
        children = [item for item in self.storage.list_children(target) if item.is_directory and item.name != "_manifests"]
        if output_folder:
            for child in children:
                if child.name == output_folder:
                    return child.id
            raise FileNotFoundError(f"Output folder does not exist: {output_folder}")
        if source:
            matches = self._find_by_source(target, source)
            if len(matches) == 1:
                return matches[0]
            if not matches:
                raise FileNotFoundError(f"No processed output matches source: {source}")
            raise ValueError(f"Source matches multiple output folders: {matches}")
        assert video_name
        matches = [child.id for child in children if any(item.name == video_name for item in self.storage.list_children(child.id))]
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise FileNotFoundError(f"No processed output contains video: {video_name}")
        raise ValueError(f"Video matches multiple output folders: {matches}")

    def _find_by_source(self, target: str, source: str) -> list[str]:
        matches = []
        manifest_root = self.storage.ensure_folder(target, "_manifests")
        children = {item.name: item for item in self.storage.list_children(target) if item.is_directory and item.name != "_manifests"}
        for item in self.storage.list_children(manifest_root):
            if item.is_directory or not item.name.lower().endswith(".json"):
                continue
            local = self._download(item, item.name)
            try:
                payload = json.loads(local.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            for entry in payload.get("entries", []) if isinstance(payload, dict) else []:
                if isinstance(entry, dict) and entry.get("source") == source and entry.get("output_folder") in children:
                    matches.append(children[entry["output_folder"]].id)
        return sorted(set(matches))

    def _resolve_video(self, candidates: list[StorageFile], preferred_name: str | None) -> StorageFile | None:
        usable = [item for item in candidates if Path(item.name).suffix.lower() in VIDEO_EXTENSIONS and "_tts" not in Path(item.name).stem.lower()]
        if preferred_name:
            usable = [item for item in usable if item.name == preferred_name]
        if not usable:
            return None
        mp4 = [item for item in usable if Path(item.name).suffix.lower() == ".mp4"]
        return sorted(mp4 or usable, key=lambda item: item.name.lower())[0]

    @staticmethod
    def _pick_vtt(files: list[StorageFile], preferred_contains: str) -> StorageFile | None:
        vtts = [item for item in files if Path(item.name).suffix.lower() == ".vtt" and ".bak" not in item.name.lower()]
        if not vtts:
            return None
        preferred = [item for item in vtts if preferred_contains.lower() in item.name.lower()]
        return sorted(preferred or vtts, key=lambda item: item.name.lower())[0]

    def _download(self, remote: StorageFile, name: str) -> Path:
        assert self._temp_root is not None
        path = self._temp_root / f"{len(list(self._temp_root.iterdir()))}_{name}"
        self.storage.download_file(remote, path)
        return path

    def _try_read_vtt(self, remote: StorageFile | None, label: str) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
        if remote is None:
            return None, {"present": False}
        local = self._download(remote, f"{label.replace(' ', '_')}.vtt")
        try:
            parsed = webvtt.read(str(local))
            segments = [{"start": c.start_in_seconds, "end": c.end_in_seconds, "text": c.text.strip()} for c in parsed]
        except Exception as exc:
            return None, {"present": True, "valid": False, "errors": [str(exc)]}
        validation = self._validate_segments(segments)
        if not validation["valid"]:
            return None, {"present": True, **validation}
        return segments, {"present": True, **validation}

    @classmethod
    def _validate_segments(cls, segments: list[dict[str, Any]]) -> dict[str, Any]:
        errors = []
        previous_end = -1.0
        for index, segment in enumerate(segments, 1):
            try:
                start = float(segment["start"])
                end = float(segment["end"])
            except (KeyError, TypeError, ValueError):
                errors.append(f"segment {index}: non-numeric timestamps")
                continue
            if start < 0 or end <= start:
                errors.append(f"segment {index}: invalid interval {start:.3f} --> {end:.3f}")
            if start + TIMESTAMP_EPSILON < previous_end:
                errors.append(f"segment {index}: overlaps previous cue")
            previous_end = max(previous_end, end)
        if not segments:
            errors.append("no segments")
        return {"valid": not errors, "errors": errors, "count": len(segments)}

    @classmethod
    def _assert_valid(cls, segments: list[dict[str, Any]], label: str) -> None:
        validation = cls._validate_segments(segments)
        if not validation["valid"]:
            raise ValueError(f"{label} failed validation: {validation['errors']}")

    def _write_temp_vtt(self, segments: list[dict[str, Any]], name: str) -> Path:
        assert self._temp_root is not None
        path = self._temp_root / name
        VTTBuilder.generate_vtt(segments, path)
        parsed = webvtt.read(str(path))
        self._assert_valid([{"start": c.start_in_seconds, "end": c.end_in_seconds, "text": c.text.strip()} for c in parsed], "generated VTT")
        return path

    def _backup_and_replace(self, current: StorageFile | None, parent: str, replacement: Path, *, fallback_name: str) -> str | None:
        target_name = current.name if current else fallback_name
        backup_name = None
        if current:
            old = self._download(current, current.name)
            backup_name = self._next_backup_name(target_name, parent)
            backup = self._temp_root / backup_name
            backup.write_bytes(old.read_bytes())
            self.storage.upload_file(backup, parent, "text/vtt")
        named = self._temp_root / target_name
        named.write_bytes(replacement.read_bytes())
        self.storage.upload_file(named, parent, "text/vtt")
        return backup_name

    def _next_backup_name(self, filename: str, parent: str) -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        candidate = f"{filename}.bak.{stamp}"
        index = 1
        while self.storage.file_exists(parent, candidate):
            candidate = f"{filename}.bak.{stamp}.{index:02d}"
            index += 1
        return candidate

    def _write_history(self, folder: str, result: dict[str, Any]) -> None:
        history = self.storage.ensure_folder(folder, self._history_name)
        path = self._temp_root / f"reprocess_{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        self.storage.upload_file(path, history, "application/json")

    @staticmethod
    def _default_original_name(video_name: str) -> str:
        return f"{Path(video_name).stem}_original.vtt"

    @staticmethod
    def diagnose_segments(segments: list[dict[str, Any]]) -> dict[str, Any]:
        gaps, overlaps = [], []
        for previous, current in zip(segments[:-1], segments[1:], strict=True):
            delta = float(current["start"]) - float(previous["end"])
            if delta > TIMESTAMP_EPSILON:
                gaps.append(delta)
            elif delta < -TIMESTAMP_EPSILON:
                overlaps.append(abs(delta))
        return {"count": len(segments), "first_start": float(segments[0]["start"]) if segments else None, "last_end": float(segments[-1]["end"]) if segments else None, "max_gap_seconds": max(gaps, default=0.0), "gap_count": len(gaps), "max_overlap_seconds": max(overlaps, default=0.0), "overlap_count": len(overlaps)}

    def _translate(self, segments, translator):
        translated = translator.translate_segments(segments)
        failed = sum(bool(item.get("translation_failed")) for item in translated)
        return translated, failed

    def _default_stt_engine(self):
        from src.stt_engine import STTEngine
        return STTEngine(self.settings)

    def _default_translator(self):
        from src.translator import TextTranslator
        return TextTranslator(self.settings)
