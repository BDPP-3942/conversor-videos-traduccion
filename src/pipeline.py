from __future__ import annotations

import logging
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from config.settings import AppSettings, local_storage_paths
from src.file_naming import (
    FileNameFormatter,
    fit_output_stem,
    normalize_comparison_key,
    normalize_component,
    normalize_filename,
)
from src.path_limits import fit_component
from src.storage.base import StorageFile, StorageProvider

logger = logging.getLogger(__name__)


class MediaPipeline:
    def __init__(self, settings: AppSettings, storage: StorageProvider) -> None:
        self.settings = settings
        self.storage = storage
        from src.extractor import ZipExtractor
        from src.media_converter import MediaConverter

        self.extractor = ZipExtractor(
            settings.max_zip_depth, settings.max_extracted_files, settings.max_extracted_size_bytes
        )
        self.media_converter = MediaConverter(settings)
        from src.media_identity import MediaIdentityResolver
        self.media_identity = MediaIdentityResolver(
            settings.ffmpeg_bin,
            settings.ffmpeg_timeout_seconds,
            settings.duplicate_name_similarity_threshold,
            settings.duplicate_duration_tolerance_seconds,
            settings.duplicate_visual_similarity_threshold,
        )
        self._thread_local = threading.local()

    def _worker_components(self):
        if not hasattr(self._thread_local, "stt_engine"):
            from src.stt_engine import STTEngine
            from src.translator import TextTranslator
            self._thread_local.stt_engine = STTEngine(self.settings)
            self._thread_local.translator = TextTranslator(self.settings)
        return self._thread_local.stt_engine, self._thread_local.translator

    def run(self, source: str, target: str) -> dict[str, Any]:
        if getattr(getattr(self, "settings", None), "normalize_legacy_names", True):
            try:
                normalize_outputs = getattr(self.storage, "normalize_existing_output_names", None)
                migration = (
                    normalize_outputs(target, self.settings.original_transcript_subdir) if normalize_outputs else {}
                )
                if migration:
                    logger.info("Normalized %d legacy output path(s)", len(migration))
            except Exception:
                logger.exception("Legacy output-name normalization failed; continuing")

        zips = self.storage.list_zip_files(source)
        if not zips:
            return {"status": "success", "message": "No ZIP files found", "zips_found": 0}

        results = []
        for zip_file in zips:
            try:
                if hasattr(self.storage, "is_processed") and self.storage.is_processed(zip_file):
                    result = (
                        self._rename_processed_zip(zip_file, target)
                        if getattr(self.settings, "rename_processed_duplicates", True)
                        else {
                            "zip": zip_file.name,
                            "status": "skipped",
                            "reason": "same source name and SHA-256 already processed",
                        }
                    )
                    if result.get("status") == "success" and result.get("rename_only"):
                        try:
                            self.storage.finalize_source(zip_file, "success", result.get("output_folders", []))
                        except FileNotFoundError as exc:
                            logger.warning("Source unavailable during rename-only finalization: %s", exc)
                else:
                    result = self._process_zip(zip_file, target)
                    if result["status"] == "success":
                        try:
                            self.storage.finalize_source(zip_file, "success", result.get("output_folders", []))
                        except FileNotFoundError as exc:
                            logger.warning("Source unavailable during finalization; keeping successful result: %s", exc)
            except Exception as exc:
                logger.exception("ZIP processing failed: %s", zip_file.name)
                result = {
                    "zip": zip_file.name,
                    "status": "error",
                    "errors": [
                        {"source": zip_file.name, "error_type": type(exc).__name__, "error": str(exc)}
                    ],
                }
            results.append(result)

        failed = sum(item["status"] == "error" for item in results)
        partial = sum(item["status"] == "partial" for item in results)
        processed = sum(item["status"] in {"success", "partial", "error"} for item in results)
        status = (
            "error"
            if failed and not any(item["status"] == "success" for item in results)
            else "partial" if failed or partial else "success"
        )
        return {
            "status": status,
            "zips_found": len(zips),
            "zips_processed": processed,
            "zips_skipped": sum(item["status"] == "skipped" for item in results),
            "zips_failed": failed,
            "zips_partial": partial,
            "zips": results,
        }

    def _manifest_path(self, zip_name: str) -> Path:
        manifest_name = fit_component(Path(zip_name).stem, local_storage_paths()["manifests"]) + ".json"
        return local_storage_paths()["manifests"] / manifest_name

    def _source_fingerprint(self, zip_file: StorageFile) -> dict[str, Any]:
        fingerprint = getattr(self.storage, "source_fingerprint", None)
        if not fingerprint:
            return {"id": zip_file.id, "name": zip_file.name}
        try:
            return fingerprint(zip_file)
        except (FileNotFoundError, OSError):
            return {"id": zip_file.id, "name": zip_file.name}

    def _process_zip(self, zip_file: StorageFile, target: str) -> dict[str, Any]:
        work_base = local_storage_paths()["work"]
        work_base.mkdir(parents=True, exist_ok=True)
        temp_prefix = fit_component(f"{Path(zip_file.name).stem}_", work_base)
        with tempfile.TemporaryDirectory(prefix=temp_prefix, dir=work_base) as temporary_dir:
            work_root = Path(temporary_dir)
            archive_target = work_root / Path(zip_file.name).name
            self.storage.download_file(zip_file, archive_target)
            extract_root = work_root / "extracted"
            extraction = self.extractor.extract_zip(archive_target, extract_root)

            from src.manifest import read_manifest, write_manifest
            manifest_path = self._manifest_path(zip_file.name)
            previous = read_manifest(manifest_path)
            previous_entries = {
                str(item.get("source")): item
                for item in previous.get("entries", [])
                if (
                    isinstance(item, dict)
                    and item.get("source")
                    and item.get("status") in {"success", "skipped_duplicate", "renamed_existing", "already_current"}
                )
            }
            media_registry = self._load_media_registry()
            source_fingerprint = self._source_fingerprint(zip_file)
            metadata = {
                "zip_name": zip_file.name,
                "source_id": zip_file.id,
                "source_fingerprint": source_fingerprint,
                "source_manifest_version": previous.get("version", 0),
                "target": target,
                "target_lang": self.settings.target_lang,
                "whisper_model": self.settings.whisper_model,
                "whisper_beam_size": self.settings.whisper_beam_size,
                "translation_batch_size": self.settings.translation_batch_size,
                "max_parallel_videos": self._effective_parallelism(),
                "resume_enabled": self.settings.resume_enabled,
                "duplicate_detection": {
                    "name_similarity_threshold": self.settings.duplicate_name_similarity_threshold,
                    "duration_tolerance_seconds": self.settings.duplicate_duration_tolerance_seconds,
                    "visual_similarity_threshold": self.settings.duplicate_visual_similarity_threshold,
                },
            }

            used_stems: set[str] = set()
            processed: list[dict[str, Any]] = []
            failed: list[dict[str, Any]] = []
            pending: list[tuple[Path, str, str]] = []

            normalized_candidates = []
            for source_path in extraction.media:
                relative_source = str(source_path.relative_to(extract_root).as_posix())
                existing_entry = previous_entries.get(relative_source)
                metadata_item = FileNameFormatter.resolve_source_metadata(source_path, extract_root)
                if self.settings.resume_enabled:
                    resumed = self._try_resume(existing_entry, target, relative_source)
                    if resumed:
                        resumed = self._rename_existing_entry_if_needed(
                            resumed, metadata_item, target, used_stems
                        )
                        resumed["resumed"] = True
                        processed.append(resumed)
                        if resumed.get("output_folder"):
                            used_stems.add(str(resumed["output_folder"]))
                        self._write_progress_manifest(manifest_path, metadata, processed, failed, write_manifest)
                        continue
                normalized_candidates.append(
                    (
                        source_path,
                        relative_source,
                        metadata_item,
                        normalize_comparison_key(source_path.name),
                    )
                )

            pending = []
            for source_path, relative_source, metadata_item, normalized_name in normalized_candidates:
                duplicate = self._find_media_duplicate(source_path, normalized_name, media_registry)
                if duplicate:
                    duplicate_entry = {
                        "source": relative_source,
                        "status": "skipped_duplicate",
                        "duplicate_of": duplicate["registry_entry"].get("source"),
                        "duplicate_of_output_folder": duplicate["registry_entry"].get("output_folder"),
                        "duplicate_match": duplicate["status"],
                        "duplicate_score": round(float(duplicate["score"]), 4),
                        "duplicate_reason": duplicate["reason"],
                        "normalized_name": normalized_name,
                    }
                    renamed = self._rename_existing_entry_if_needed(
                        duplicate["registry_entry"], metadata_item, target, used_stems
                    )
                    if renamed.get("output_folder"):
                        duplicate_entry.update({
                            "status": "renamed_existing",
                            "output_folder": renamed["output_folder"],
                            "output_relative_path": renamed.get("output_relative_path"),
                            "rename_only": True,
                            "name_metadata": renamed.get("name_metadata"),
                            "video": renamed.get("video"),
                            "secondary_video": renamed.get("secondary_video"),
                            "audio": renamed.get("audio"),
                            "translated_vtt": renamed.get("translated_vtt"),
                            "original_transcription": renamed.get("original_transcription"),
                        })
                    processed.append(duplicate_entry)
                    logger.info(
                        "Skipping duplicate processing %s -> %s (%s, score=%.2f)%s",
                        relative_source,
                        duplicate_entry.get("duplicate_of"),
                        duplicate_entry["duplicate_match"],
                        duplicate_entry["duplicate_score"],
                        " and renaming existing output" if duplicate_entry.get("rename_only") else "",
                    )
                    self._write_progress_manifest(manifest_path, metadata, processed, failed, write_manifest)
                    continue
                stem = self._allocate_stem(
                    metadata_item.output_stem,
                    used_stems,
                    target,
                    source_path,
                    extract_root,
                    work_root,
                )
                pending.append((source_path, relative_source, stem, normalized_name, metadata_item))

            if pending:
                workers = self._effective_parallelism()
                logger.info("Processing %d remaining video(s) with %d worker(s)", len(pending), workers)
                if workers == 1:
                    for source_path, relative_source, stem, normalized_name, metadata_item in pending:
                        try:
                            item = self._process_media(
                                source_path, extract_root, work_root, target, stem, normalized_name, metadata_item
                            )
                            item["resumed"] = False
                            processed.append(item)
                            self._register_media_identity(source_path, normalized_name, item)
                        except Exception as exc:
                            self._record_failure(zip_file, source_path, relative_source, exc, failed)
                        self._write_progress_manifest(manifest_path, metadata, processed, failed, write_manifest)
                else:
                    futures = {}
                    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="video-worker") as executor:
                        for source_path, relative_source, stem, normalized_name, metadata_item in pending:
                            future = executor.submit(
                                self._process_media,
                                source_path,
                                extract_root,
                                work_root,
                                target,
                                stem,
                                normalized_name,
                                metadata_item,
                            )
                            futures[future] = (source_path, relative_source)
                        for future in as_completed(futures):
                            source_path, relative_source = futures[future]
                            try:
                                item = future.result()
                                item["resumed"] = False
                                processed.append(item)
                                self._register_media_identity(
                                    source_path,
                                    item.get("normalized_name", normalize_comparison_key(source_path.name)),
                                    item,
                                )
                            except Exception as exc:
                                self._record_failure(zip_file, source_path, relative_source, exc, failed)
                            self._write_progress_manifest(manifest_path, metadata, processed, failed, write_manifest)

            status = "success" if processed and not failed else "partial" if processed else "error"
            result = {
                "zip": zip_file.name,
                "status": status,
                "media_found": len(extraction.media),
                "media_processed": sum(item.get("status") == "success" for item in processed),
                "media_resumed": sum(item.get("resumed", False) for item in processed),
                "media_skipped_duplicates": sum(item.get("status") == "skipped_duplicate" for item in processed),
                "media_failed": len(failed),
                "parallel_workers": self._effective_parallelism(),
                "nested_zips": len(extraction.nested_zips),
                "ignored_files": len(extraction.ignored_files),
                "max_zip_depth": extraction.max_depth_reached,
                "extracted_files": extraction.extracted_files,
                "extracted_bytes": extraction.extracted_bytes,
                "videos": sorted(processed, key=lambda item: str(item.get("source", ""))),
                "errors": failed,
                "output_folders": sorted(
                    {str(item["output_folder"]) for item in processed if item.get("output_folder")}
                ),
            }
            self._write_progress_manifest(manifest_path, metadata, processed, failed, write_manifest)
            if self.settings.provider.lower() in {"google_drive", "gdrive"}:
                self.storage.upload_file(manifest_path, target, "application/json")
            return result

    def _effective_parallelism(self) -> int:
        configured = max(1, int(self.settings.max_parallel_videos))
        if self.settings.provider.lower() not in {"local"}:
            return 1
        return configured

    def _record_failure(self, zip_file, source_path, relative_source, exc, failed):
        logger.exception("Media processing failed: %s", source_path.name)
        failure = {"source": relative_source, "error_type": type(exc).__name__, "error": str(exc), "status": "error"}
        failed.append(failure)
        self._write_failure(zip_file.name, source_path.name, failure)

    def _write_progress_manifest(self, path, metadata, processed, failed, writer) -> None:
        writer(path, processed + failed, metadata=metadata)

    def _try_resume(
        self, existing_entry: dict[str, Any] | None, target: str, relative_source: str
    ) -> dict[str, Any] | None:
        if (
            not existing_entry
            or existing_entry.get("status") not in {"success", "renamed_existing", "already_current"}
            or existing_entry.get("source") != relative_source
        ):
            return None
        folder = normalize_component(str(existing_entry.get("output_folder", "")))
        if not folder:
            return None
        if not self.storage.folder_exists(target, folder):
            return None
        output_folder = self.storage.ensure_folder(target, folder)
        original_folder = self.storage.ensure_folder(output_folder, self.settings.original_transcript_subdir)
        video_raw = str(existing_entry.get("video", "")).strip()
        secondary_raw = str(existing_entry.get("secondary_video", "")).strip()
        audio_raw = str(existing_entry.get("audio", "")).strip()
        translated_raw = str(existing_entry.get("translated_vtt", "")).strip()
        original_raw = str(existing_entry.get("original_transcription", "")).strip()
        video = normalize_filename(video_raw) if video_raw else ""
        secondary = normalize_filename(secondary_raw) if secondary_raw else ""
        audio = normalize_filename(audio_raw) if audio_raw else ""
        translated_vtt = normalize_filename(translated_raw) if translated_raw else ""
        original = normalize_filename(original_raw) if original_raw else ""
        if not video or not translated_vtt or not original:
            return None
        required = [video, translated_vtt]
        if secondary:
            required.append(secondary)
        if audio:
            required.append(audio)
        if not all(self.storage.file_exists(output_folder, name) for name in required):
            return None
        if not self.storage.file_exists(original_folder, original):
            return None
        resumed = dict(existing_entry)
        resumed.update(
            {
                "output_folder": folder,
                "video": video,
                "secondary_video": secondary,
                "audio": audio,
                "translated_vtt": translated_vtt,
                "original_transcription": original,
                "output_relative_path": f"{folder}/{video}",
                "source": relative_source,
            }
        )
        return resumed

    def _process_media(
        self,
        source_path: Path,
        extract_root: Path,
        work_root: Path,
        target: str,
        stem: str,
        normalized_name: str,
        metadata_item,
    ) -> dict[str, Any]:
        stt_engine, translator = self._worker_components()
        processed_dir = work_root / "processed" / stem
        processed_dir.mkdir(parents=True, exist_ok=True)
        artifacts = self.media_converter.convert(source_path, stem, processed_dir)
        segments = stt_engine.transcribe(artifacts.mp4_path)
        if not segments:
            raise RuntimeError(f"No STT segments generated for {source_path.name}")

        transcription_dir = work_root / "transcriptions_original" / stem
        transcription_dir.mkdir(parents=True, exist_ok=True)
        original_path = transcription_dir / f"{stem}_original.vtt"
        from src.vtt_builder import VTTBuilder
        VTTBuilder.generate_vtt(segments, original_path)

        translated = translator.translate_segments(segments)
        translated_path = work_root / f"{stem}_{self.settings.target_lang.lower()}.vtt"
        VTTBuilder.generate_vtt(translated, translated_path)

        output_folder = self.storage.ensure_folder(target, stem)
        original_target = self.storage.ensure_folder(output_folder, self.settings.original_transcript_subdir)
        secondary_mime = (
            "video/webm"
            if artifacts.secondary_video_path.suffix.lower() == ".webm"
            else "video/x-matroska"
        )
        for local_path, mime in (
            (artifacts.mp4_path, "video/mp4"),
            (artifacts.secondary_video_path, secondary_mime),
            (translated_path, "text/vtt"),
        ):
            self.storage.upload_file(local_path, output_folder, mime)
        self.storage.upload_file(original_path, original_target, "text/vtt")

        return {
            "source": str(source_path.relative_to(extract_root)),
            "video": artifacts.mp4_path.name,
            "secondary_video": artifacts.secondary_video_path.name,
            "translated_vtt": translated_path.name,
            "original_transcription": original_path.name,
            "output_folder": stem,
            "output_relative_path": f"{stem}/{artifacts.mp4_path.name}",
            "segments": len(translated),
            "status": "success",
            "normalized_name": normalized_name,
            "name_metadata": {
                "course": metadata_item.course,
                "lesson": metadata_item.lesson,
                "course_name": metadata_item.course_name,
                "lesson_name": metadata_item.lesson_name,
                "description": metadata_item.description,
                "output_stem": metadata_item.output_stem,
                "confidence": metadata_item.confidence,
                "review_required": metadata_item.review_required,
                "review_reason": metadata_item.review_reason,
            },
        }

    def _rename_processed_zip(self, zip_file: StorageFile, target: str) -> dict[str, Any]:
        work_base = local_storage_paths()["work"]
        work_base.mkdir(parents=True, exist_ok=True)
        temp_prefix = fit_component(f"rename_{Path(zip_file.name).stem}_", work_base)
        from src.manifest import read_manifest, write_manifest
        manifest_path = self._manifest_path(zip_file.name)
        previous = read_manifest(manifest_path)
        previous_entries = {
            str(item.get("source")): item
            for item in previous.get("entries", [])
            if isinstance(item, dict) and item.get("source") and item.get("status") in {"success", "renamed_existing"}
        }
        with tempfile.TemporaryDirectory(prefix=temp_prefix, dir=work_base) as temporary_dir:
            work_root = Path(temporary_dir)
            archive_target = work_root / Path(zip_file.name).name
            self.storage.download_file(zip_file, archive_target)
            extraction = self.extractor.extract_zip(archive_target, work_root / "extracted")
            used_stems: set[str] = set()
            processed: list[dict[str, Any]] = []
            unresolved: list[dict[str, Any]] = []
            for source_path in extraction.media:
                relative_source = str(source_path.relative_to(work_root / "extracted").as_posix())
                entry = previous_entries.get(relative_source)
                metadata_item = FileNameFormatter.resolve_source_metadata(source_path, work_root / "extracted")
                if not entry:
                    unresolved.append({"source": relative_source, "status": "not_found_in_previous_manifest"})
                    continue
                try:
                    renamed = self._rename_existing_entry_if_needed(entry, metadata_item, target, used_stems)
                    renamed["source"] = relative_source
                    renamed["rename_only"] = True
                    processed.append(renamed)
                except Exception as exc:
                    logger.exception("Rename-only migration failed for %s", relative_source)
                    unresolved.append({"source": relative_source, "status": "error", "error": str(exc)})
            status = "success" if processed and not unresolved else "partial" if processed else "error"
            result = {
                "zip": zip_file.name,
                "status": status,
                "rename_only": True,
                "media_found": len(extraction.media),
                "media_renamed": sum(item.get("status") == "renamed_existing" for item in processed),
                "media_skipped": sum(item.get("status") == "already_current" for item in processed),
                "errors": unresolved,
                "videos": processed,
                "output_folders": sorted(
                    {str(item["output_folder"]) for item in processed if item.get("output_folder")}
                ),
            }
            self._write_progress_manifest(
                manifest_path,
                {
                    "zip_name": zip_file.name,
                    "rename_only": True,
                    "target": target,
                    "target_lang": self.settings.target_lang,
                },
                processed,
                unresolved,
                write_manifest,
            )
            if self.settings.provider.lower() in {"google_drive", "gdrive"}:
                self.storage.upload_file(manifest_path, target, "application/json")
            return result

    def _rename_existing_entry_if_needed(
        self, entry: dict[str, Any], metadata_item, target: str, used_stems: set[str]
    ) -> dict[str, Any]:
        old_folder = normalize_component(str(entry.get("output_folder", "")))
        if not old_folder or not self.storage.folder_exists(target, old_folder):
            return {}
        desired = normalize_component(str(metadata_item.output_stem))
        new_folder = self._allocate_rename_stem(desired, old_folder, used_stems, target)
        result = dict(entry)
        if new_folder == old_folder:
            result.update({
                "status": "already_current",
                "output_folder": old_folder,
                "video": normalize_filename(str(entry.get("video", ""))),
                "secondary_video": normalize_filename(str(entry.get("secondary_video", ""))),
                "audio": normalize_filename(str(entry.get("audio", ""))),
                "translated_vtt": normalize_filename(str(entry.get("translated_vtt", ""))),
                "original_transcription": normalize_filename(str(entry.get("original_transcription", ""))),
                "output_relative_path": f"{old_folder}/{normalize_filename(str(entry.get('video', '')))}",
            })
            result["name_metadata"] = self._name_metadata(metadata_item)
            used_stems.add(old_folder)
            return result

        self.storage.rename_output_folder(target, old_folder, new_folder, self.settings.original_transcript_subdir)
        for key in ("video", "secondary_video", "audio", "translated_vtt", "original_transcription"):
            value = normalize_filename(str(entry.get(key, "")))
            if value:
                result[key] = self._rename_artifact_filename(value, old_folder, new_folder)
        result.update({
            "status": "renamed_existing",
            "output_folder": new_folder,
            "output_relative_path": f"{new_folder}/{result.get('video', '')}",
            "rename_only": True,
            "name_metadata": self._name_metadata(metadata_item),
        })
        self._update_media_registry_folder(old_folder, new_folder)
        used_stems.add(new_folder)
        return result

    def _allocate_rename_stem(self, desired: str, old_folder: str, used_stems: set[str], target: str) -> str:
        if desired == old_folder:
            return old_folder
        if desired not in used_stems and not self.storage.folder_exists(target, desired):
            return desired
        suffix_source = old_folder[:8] or "legacy"
        candidate = f"{desired}_{suffix_source}"
        index = 2
        while candidate in used_stems or (self.storage.folder_exists(target, candidate) and candidate != old_folder):
            candidate = f"{desired}_{suffix_source}_{index:02d}"
            index += 1
        return candidate

    @staticmethod
    def _rename_artifact_filename(filename: str, old_stem: str, new_stem: str) -> str:
        path = Path(filename)
        stem = path.stem
        if stem.startswith(old_stem):
            stem = new_stem + stem[len(old_stem):]
        else:
            stem = normalize_component(stem)
        return f"{stem}{path.suffix.lower()}"

    @staticmethod
    def _name_metadata(metadata_item) -> dict[str, Any]:
        return {
            "course": metadata_item.course,
            "lesson": metadata_item.lesson,
            "course_name": metadata_item.course_name,
            "lesson_name": metadata_item.lesson_name,
            "description": metadata_item.description,
            "output_stem": metadata_item.output_stem,
            "confidence": metadata_item.confidence,
            "review_required": metadata_item.review_required,
            "review_reason": metadata_item.review_reason,
        }

    def _media_registry_path(self) -> Path:
        return local_storage_paths()["state"] / "media_registry.jsonl"

    def _load_media_registry(self) -> list[dict[str, Any]]:
        path = self._media_registry_path()
        if not path.is_file():
            return []
        import json

        entries = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict) and value.get("status") == "success":
                entries.append(value)
        return entries

    def _find_media_duplicate(
        self, source_path: Path, normalized_name: str, registry: list[dict[str, Any]]
    ):
        from src.media_identity import MediaIdentityResolver
        from src.storage.processed_registry import sha256_file

        # Exact duplicates are resolved with one sequential SHA-256 pass, avoiding
        # the much more expensive ffmpeg probe + visual/audio sampling path.
        digest = sha256_file(source_path)
        for entry in registry:
            if entry.get("sha256") == digest and entry.get("output_folder"):
                return {
                    "status": "duplicate_exact",
                    "score": 1.0,
                    "reason": "Exact SHA-256 match in the processed media registry.",
                    "registry_entry": entry,
                }

        candidates = MediaIdentityResolver.candidate_names(registry, normalized_name)
        if not candidates:
            return None
        match = self.media_identity.find_duplicate(source_path, normalized_name, candidates)
        return match.__dict__ if match else None

    def _update_media_registry_folder(self, old_name: str, new_name: str) -> None:
        import json
        path = self._media_registry_path()
        if not path.is_file():
            return
        lines = path.read_text(encoding="utf-8").splitlines()
        changed = False
        output: list[str] = []
        for line in lines:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                output.append(line)
                continue
            if isinstance(item, dict) and item.get("output_folder") == old_name:
                item["output_folder"] = new_name
                changed = True
            output.append(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
        if changed:
            path.write_text("\n".join(output) + "\n", encoding="utf-8")

    def _register_media_identity(self, source_path: Path, normalized_name: str, item: dict[str, Any]) -> None:
        import json

        try:
            identity = self.media_identity.build_identity(source_path)
        except Exception:
            logger.exception("Could not persist media identity for %s", source_path.name)
            return
        payload = {
            "status": "success",
            "source": item.get("source"),
            "output_folder": item.get("output_folder"),
            "video": item.get("video"),
            "normalized_name": normalized_name,
            **identity.to_dict(),
        }
        path = self._media_registry_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")

    def _allocate_stem(
        self, base: str, used: set[str], target: str, source_path: Path, extract_root: Path, work_root: Path
    ) -> str:
        parent = local_storage_paths()["output"] if self.settings.provider.lower() == "local" else work_root
        reserve = (f"_{self.settings.target_lang.lower()}.vtt", "_original.vtt")
        candidate = fit_output_stem(base, parent, reserve_suffixes=reserve)
        if candidate not in used and not self.storage.folder_exists(target, candidate):
            used.add(candidate)
            return candidate
        from src.storage.processed_registry import sha256_file

        digest = sha256_file(source_path)[:8]
        candidate = fit_output_stem(base, parent, digest, reserve_suffixes=reserve)
        index = 2
        while candidate in used or self.storage.folder_exists(target, candidate):
            candidate = fit_output_stem(base, parent, f"{digest}_{index:02d}", reserve_suffixes=reserve)
            index += 1
        used.add(candidate)
        return candidate

    @staticmethod
    def _write_failure(zip_name: str, media_name: str, failure: dict[str, Any]) -> None:
        failure_dir = local_storage_paths()["failures"]
        failure_dir.mkdir(parents=True, exist_ok=True)
        base = f"{Path(zip_name).stem}_{Path(media_name).stem}"
        failure_path = failure_dir / (fit_component(base, failure_dir) + ".json")
        from src.manifest import write_manifest
        write_manifest(failure_path, [failure], metadata={"type": "media_failure"})

    def cleanup(self) -> None:
        return
