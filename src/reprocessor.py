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
    """Reprocess subtitle artefacts in an existing output folder without invoking media conversion."""

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
            raise ValueError(
                "A concrete reprocess target is required for reprocess(); use reprocess_all() for the general case"
            )

        self._temp_root = Path(tempfile.mkdtemp(prefix="subtitle-reprocess-"))
        try:
            folder = self._resolve_output_folder(target, output_folder, video_name, source)
            files = self.storage.list_children(folder)
            candidates = [item for item in files if not item.is_directory]
            video = self._resolve_video(candidates, video_name)
            original_subdir = self.storage.ensure_folder(folder, self.settings.original_transcript_subdir)
            original_files = [item for item in self.storage.list_children(original_subdir) if not item.is_directory]
            original_vtt = self._pick_vtt(original_files, preferred_contains="_original")
            translated_vtt = self._pick_vtt(candidates, preferred_contains=f"_{self.settings.target_lang.lower()}")

            if mode in {"stt_only", "full"} and video is None:
                raise FileNotFoundError(f"No reusable video found in output folder: {folder}")
            if mode == "translate_only" and original_vtt is None:
                raise FileNotFoundError(
                    f"No existing original transcription found in {self.settings.original_transcript_subdir}/"
                )

            old_original_segments = (
                self._read_vtt_segments(original_vtt, "existing transcription") if original_vtt else []
            )
            diagnostics_before = self.diagnose_segments(old_original_segments) if old_original_segments else {}

            if mode == "translate_only":
                translated_segments, translation_failed = self._translate(old_original_segments, translator_factory)
                validation = self._validate_segments(translated_segments, previous_count=len(old_original_segments))
                if not validation["valid"]:
                    raise ValueError(f"New translation failed validation: {validation['errors']}")
                new_translated = self._write_temp_vtt(translated_segments, "translated.vtt")
                fallback_translation_name = (
                    f"{Path(original_vtt.name).stem.removesuffix('_original')}_{self.settings.target_lang.lower()}.vtt"
                    if original_vtt
                    else None
                )
                backup_translated = self._backup_and_replace(
                    translated_vtt,
                    folder,
                    new_translated,
                    mime_type="text/vtt",
                    fallback_name=fallback_translation_name,
                )
                status = "partial_translation" if translation_failed else "success"
                result = {
                    "operation": "reprocess_subtitles",
                    "mode": "translate_only",
                    "status": status,
                    "output_folder": folder,
                    "video": video.name if video else None,
                    "previous_transcription": original_vtt.name if original_vtt else None,
                    "translated_vtt": translated_vtt.name if translated_vtt else new_translated.name,
                    "backup": backup_translated,
                    "segments": len(translated_segments),
                    "translation_failed_segments": translation_failed,
                    "timestamp_diagnostics": diagnostics_before,
                    "translation_preserves_timing": True,
                }
            else:
                video_local = self._download(video, "source.mp4")
                engine = stt_engine_factory() if stt_engine_factory else self._default_stt_engine()
                segments = engine.transcribe(video_local)
                validation = self._validate_segments(segments, previous_count=len(old_original_segments))
                if not validation["valid"]:
                    raise ValueError(f"New STT output failed validation: {validation['errors']}")
                diagnostics_after = self.diagnose_segments(segments)
                new_original = self._write_temp_vtt(segments, "original.vtt")
                translated_segments: list[dict[str, Any]] = []
                translation_failed = 0
                new_translated: Path | None = None
                if mode == "full":
                    translator = translator_factory() if translator_factory else self._default_translator()
                    translated_segments = translator.translate_segments(segments)
                    translation_failed = sum(bool(segment.get("translation_failed")) for segment in translated_segments)
                    translation_validation = self._validate_segments(
                        translated_segments,
                        previous_count=len(self._read_vtt_segments(translated_vtt, "existing translation"))
                        if translated_vtt
                        else len(segments),
                    )
                    if not translation_validation["valid"]:
                        raise ValueError(f"New translated VTT failed validation: {translation_validation['errors']}")
                    new_translated = self._write_temp_vtt(translated_segments, "translated.vtt")

                # Both new artefacts have now passed validation. Only now can any existing artefact be replaced.
                backup_original = self._backup_and_replace(
                    original_vtt,
                    original_subdir,
                    new_original,
                    mime_type="text/vtt",
                    fallback_name=self._default_original_name(video.name),
                )
                backup_translated = None
                if mode == "full" and new_translated is not None:
                    backup_translated = self._backup_and_replace(
                        translated_vtt,
                        folder,
                        new_translated,
                        mime_type="text/vtt",
                        fallback_name=f"{Path(video.name).stem}_{self.settings.target_lang.lower()}.vtt",
                    )

                result = {
                    "operation": "reprocess_subtitles",
                    "mode": mode,
                    "status": "partial_translation" if translation_failed else "success",
                    "output_folder": folder,
                    "video": video.name,
                    "previous_transcription": original_vtt.name if original_vtt else None,
                    "new_transcription": self._default_original_name(video.name),
                    "backup_transcription": backup_original,
                    "translated_vtt": (
                        translated_vtt.name
                        if translated_vtt
                        else f"{Path(video.name).stem}_{self.settings.target_lang.lower()}.vtt"
                    )
                    if mode == "full"
                    else None,
                    "backup_translated_vtt": backup_translated,
                    "segments": len(segments),
                    "translation_failed_segments": translation_failed,
                    "timestamp_diagnostics_before": diagnostics_before,
                    "timestamp_diagnostics_after": diagnostics_after,
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

    def reprocess_all(
        self,
        target: str,
        *,
        mode: str,
        stt_engine_factory: Callable[[], Any] | None = None,
        translator_factory: Callable[[], Any] | None = None,
    ) -> dict[str, Any]:
        """Reprocess every existing output folder eligible for subtitle work.

        This intentionally operates only on already existing output folders. It never
        creates a new output folder, runs normal deduplication, or invokes FFmpeg.
        Each folder is isolated so one bad result does not abort the whole batch.
        """
        mode = mode.lower().replace("-", "_")
        if mode not in {"stt_only", "translate_only", "full"}:
            raise ValueError(f"Unsupported reprocess mode: {mode}")

        folders = self._list_reprocessable_folders(target)
        results: list[dict[str, Any]] = []
        failures = 0
        partial_translation = 0
        for folder in folders:
            try:
                result = self.reprocess(
                    target,
                    mode=mode,
                    output_folder=folder,
                    stt_engine_factory=stt_engine_factory,
                    translator_factory=translator_factory,
                )
            except Exception as exc:
                failures += 1
                result = {
                    "operation": "reprocess_subtitles",
                    "mode": mode,
                    "status": "error",
                    "output_folder": folder,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
                logger.exception("Reprocess failed for output folder %s", folder)
            else:
                if result.get("status") == "partial_translation":
                    partial_translation += 1
            results.append(result)

        if failures:
            status = "partial_failure" if results and len(results) > failures else "error"
        elif partial_translation:
            status = "partial_translation"
        else:
            status = "success"

        return {
            "operation": "reprocess_subtitles",
            "scope": "all",
            "mode": mode,
            "status": status,
            "total_candidates": len(folders),
            "processed": len(folders) - failures,
            "failed": failures,
            "partial_translation": partial_translation,
            "results": results,
        }

    def _list_reprocessable_folders(self, target: str) -> list[str]:
        folders: list[str] = []
        for child in self.storage.list_children(target):
            if not child.is_directory or child.name == "_manifests":
                continue
            child_items = self.storage.list_children(child.id)
            children = [item for item in child_items if not item.is_directory]
            has_video = any(Path(item.name).suffix.lower() in VIDEO_EXTENSIONS for item in children)
            transcript_folder = next(
                (
                    item
                    for item in child_items
                    if item.is_directory and item.name == self.settings.original_transcript_subdir
                ),
                None,
            )
            transcript_files = []
            if transcript_folder is not None:
                transcript_files = [
                    item
                    for item in self.storage.list_children(transcript_folder.id)
                    if not item.is_directory
                    and Path(item.name).suffix.lower() == ".vtt"
                    and ".bak" not in item.name.lower()
                ]
            if has_video or transcript_files:
                folders.append(child.name)
        return sorted(folders, key=str.lower)

    def _resolve_output_folder(
        self, target: str, output_folder: str | None, video_name: str | None, source: str | None
    ) -> str:
        if output_folder:
            if not self.storage.folder_exists(target, output_folder):
                raise FileNotFoundError(f"Output folder does not exist: {output_folder}")
            return output_folder

        if source:
            matches = self._find_by_source(target, source)
            if len(matches) == 1:
                return matches[0]
            if not matches:
                raise FileNotFoundError(f"No processed output matches source: {source}")
            raise ValueError(f"Source matches multiple output folders: {matches}")

        assert video_name
        matches = []
        for child in self.storage.list_children(target):
            if child.is_directory and child.name != "_manifests":
                if any(item.name == video_name for item in self.storage.list_children(child.id)):
                    matches.append(child.id)
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise FileNotFoundError(f"No processed output contains video: {video_name}")
        raise ValueError(f"Video matches multiple output folders: {[str(item) for item in matches]}")

    def _find_by_source(self, target: str, source: str) -> list[str]:
        matches: list[str] = []
        manifest_root = self.storage.ensure_folder(target, "_manifests")
        for item in self.storage.list_children(manifest_root):
            if item.is_directory or not item.name.lower().endswith(".json"):
                continue
            local = self._download(item, item.name)
            try:
                payload = json.loads(local.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            for entry in payload.get("entries", []) if isinstance(payload, dict) else []:
                if not isinstance(entry, dict) or entry.get("source") != source:
                    continue
                folder = str(entry.get("output_folder", "")).strip()
                if folder and self.storage.folder_exists(target, folder):
                    matches.append(folder)
        return sorted(set(matches))

    def _resolve_video(self, candidates: list[StorageFile], preferred_name: str | None) -> StorageFile | None:
        usable = [item for item in candidates if Path(item.name).suffix.lower() in VIDEO_EXTENSIONS]
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

    def _write_temp_vtt(self, segments: list[dict[str, Any]], name: str) -> Path:
        assert self._temp_root is not None
        path = self._temp_root / name
        VTTBuilder.generate_vtt(segments, path)
        if not path.is_file() or path.stat().st_size <= 0:
            raise ValueError(f"Generated VTT is empty: {path}")
        try:
            parsed = webvtt.read(str(path))
            parsed_segments = [
                {
                    "start": caption.start_in_seconds,
                    "end": caption.end_in_seconds,
                    "text": caption.text.strip(),
                }
                for caption in parsed
            ]
        except Exception as exc:
            raise ValueError(f"Generated VTT is not syntactically valid: {exc}") from exc
        validation = self._validate_segments(parsed_segments)
        if not validation["valid"]:
            raise ValueError(f"Generated VTT failed validation: {validation['errors']}")
        return path

    def _backup_and_replace(
        self,
        current: StorageFile | None,
        parent: str,
        replacement: Path,
        *,
        mime_type: str,
        fallback_name: str | None = None,
    ) -> str | None:
        target_name = current.name if current else fallback_name
        if not target_name:
            raise FileNotFoundError("Cannot determine target VTT filename")

        if current:
            current_local = self._download(current, current.name)
            backup_name = self._next_backup_name(target_name, parent)
            backup_path = self._temp_root / backup_name
            backup_path.write_bytes(current_local.read_bytes())
            self.storage.upload_file(backup_path, parent, "text/vtt")
        else:
            backup_name = None

        replacement_named = self._temp_root / target_name
        replacement_named.write_bytes(replacement.read_bytes())
        self.storage.upload_file(replacement_named, parent, mime_type)
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
        history_folder = self.storage.ensure_folder(folder, self._history_name)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        path = self._temp_root / f"reprocess_{timestamp}.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        self.storage.upload_file(path, history_folder, "application/json")

    @staticmethod
    def _default_original_name(video_name: str) -> str:
        return f"{Path(video_name).stem}_original.vtt"

    @staticmethod
    def diagnose_segments(segments: list[dict[str, Any]]) -> dict[str, Any]:
        if not segments:
            return {"count": 0}
        gaps: list[float] = []
        overlaps: list[float] = []
        for previous, current in zip(segments[:-1], segments[1:], strict=True):
            gap = float(current["start"]) - float(previous["end"])
            if gap > TIMESTAMP_EPSILON:
                gaps.append(gap)
            elif gap < -TIMESTAMP_EPSILON:
                overlaps.append(abs(gap))
        return {
            "count": len(segments),
            "first_start": float(segments[0]["start"]),
            "last_end": float(segments[-1]["end"]),
            "max_gap_seconds": max(gaps, default=0.0),
            "gap_count": len(gaps),
            "max_overlap_seconds": max(overlaps, default=0.0),
            "overlap_count": len(overlaps),
        }

    @classmethod
    def _validate_segments(cls, segments: list[dict[str, Any]], previous_count: int = 0) -> dict[str, Any]:
        errors: list[str] = []
        try:
            VTTBuilder.validate_segments(segments)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(str(exc))

        previous_start = -1.0
        previous_end = -1.0
        for index, segment in enumerate(segments, start=1):
            try:
                start = float(segment["start"])
                end = float(segment["end"])
            except (KeyError, TypeError, ValueError):
                errors.append(f"segment {index}: non-numeric timestamps")
                continue
            if start + TIMESTAMP_EPSILON < previous_start:
                errors.append(f"segment {index}: timestamps are not ordered")
            if start + TIMESTAMP_EPSILON < previous_end and previous_end - start > 10:
                errors.append(f"segment {index}: impossible overlap >10 seconds")
            previous_start, previous_end = start, end

        if not segments:
            errors.append("no segments generated")
        if previous_count and len(segments) > previous_count * 10 + 100:
            errors.append(f"segment count {len(segments)} is implausibly high versus previous {previous_count}")
        if len(segments) > 100_000:
            errors.append("segment count exceeds safety limit")
        return {"valid": not errors, "errors": errors, "count": len(segments)}

    def _read_vtt_segments(self, remote: StorageFile | None, label: str) -> list[dict[str, Any]]:
        if remote is None:
            return []
        local = self._download(remote, f"{label.replace(' ', '_')}.vtt")
        try:
            parsed = webvtt.read(str(local))
        except Exception as exc:
            raise ValueError(f"Invalid existing VTT {remote.name}: {exc}") from exc
        segments = [
            {"start": caption.start_in_seconds, "end": caption.end_in_seconds, "text": caption.text.strip()}
            for caption in parsed
        ]
        validation = self._validate_segments(segments)
        if not validation["valid"]:
            raise ValueError(f"Existing VTT {label} is invalid: {validation['errors']}")
        return segments

    def _translate(
        self, segments: list[dict[str, Any]], factory: Callable[[], Any] | None
    ) -> tuple[list[dict[str, Any]], int]:
        translator = factory() if factory else self._default_translator()
        translated = translator.translate_segments(segments)
        failed = sum(bool(segment.get("translation_failed")) for segment in translated)
        return translated, failed

    def _default_stt_engine(self):
        from src.stt_engine import STTEngine

        return STTEngine(self.settings)

    def _default_translator(self):
        from src.translator import TextTranslator

        return TextTranslator(self.settings)
