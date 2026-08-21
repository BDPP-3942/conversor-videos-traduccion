from __future__ import annotations

import hashlib
import logging
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from config.settings import AppSettings, local_storage_paths
from src.file_naming import FileNameFormatter, fit_output_stem, normalize_component, normalize_filename
from src.path_limits import fit_component
from src.storage.base import StorageFile, StorageProvider

logger = logging.getLogger(__name__)


class MediaPipeline:
    def __init__(self, settings: AppSettings, storage: StorageProvider) -> None:
        self.settings = settings
        self.storage = storage
        from src.extractor import ZipExtractor
        from src.media_converter import MediaConverter

        self.extractor = ZipExtractor(settings.max_zip_depth, settings.max_extracted_files, settings.max_extracted_size_bytes)
        self.media_converter = MediaConverter(settings)
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
                migration = normalize_outputs(target, self.settings.original_transcript_subdir) if normalize_outputs else {}
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
                    result = {"zip": zip_file.name, "status": "skipped", "reason": "same source name and SHA-256 already processed"}
                else:
                    result = self._process_zip(zip_file, target)
                    if result["status"] == "success":
                        try:
                            self.storage.finalize_source(zip_file, "success", result.get("output_folders", []))
                        except FileNotFoundError as exc:
                            logger.warning("Source unavailable during finalization; keeping successful result: %s", exc)
            except Exception as exc:
                logger.exception("ZIP processing failed: %s", zip_file.name)
                result = {"zip": zip_file.name, "status": "error", "errors": [{"source": zip_file.name, "error_type": type(exc).__name__, "error": str(exc)}]}
            results.append(result)

        failed = sum(item["status"] == "error" for item in results)
        partial = sum(item["status"] == "partial" for item in results)
        processed = sum(item["status"] in {"success", "partial", "error"} for item in results)
        status = "error" if failed and not any(item["status"] == "success" for item in results) else "partial" if failed or partial else "success"
        return {"status": status, "zips_found": len(zips), "zips_processed": processed, "zips_skipped": sum(item["status"] == "skipped" for item in results), "zips_failed": failed, "zips_partial": partial, "zips": results}

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
            previous_entries = {str(item.get("source")): item for item in previous.get("entries", []) if isinstance(item, dict) and item.get("source") and item.get("status") == "success"}
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
            }

            used_stems: set[str] = set()
            processed: list[dict[str, Any]] = []
            failed: list[dict[str, Any]] = []
            pending: list[tuple[Path, str, str]] = []

            for source_path in extraction.media:
                relative_source = str(source_path.relative_to(extract_root).as_posix())
                existing_entry = previous_entries.get(relative_source)
                if self.settings.resume_enabled:
                    resumed = self._try_resume(existing_entry, target, relative_source)
                    if resumed:
                        resumed["resumed"] = True
                        processed.append(resumed)
                        used_stems.add(str(resumed["output_folder"]))
                        self._write_progress_manifest(manifest_path, metadata, processed, failed, write_manifest)
                        continue
                metadata_item = FileNameFormatter.resolve_source_metadata(source_path, extract_root)
                stem = self._allocate_stem(metadata_item.output_stem, used_stems, target, source_path, extract_root, work_root)
                pending.append((source_path, relative_source, stem))

            if pending:
                workers = self._effective_parallelism()
                logger.info("Processing %d remaining video(s) with %d worker(s)", len(pending), workers)
                if workers == 1:
                    for source_path, relative_source, stem in pending:
                        try:
                            item = self._process_media(source_path, extract_root, work_root, target, stem)
                            item["resumed"] = False
                            processed.append(item)
                        except Exception as exc:
                            self._record_failure(zip_file, source_path, relative_source, exc, failed)
                        self._write_progress_manifest(manifest_path, metadata, processed, failed, write_manifest)
                else:
                    futures = {}
                    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="video-worker") as executor:
                        for source_path, relative_source, stem in pending:
                            future = executor.submit(self._process_media, source_path, extract_root, work_root, target, stem)
                            futures[future] = (source_path, relative_source)
                        for future in as_completed(futures):
                            source_path, relative_source = futures[future]
                            try:
                                item = future.result()
                                item["resumed"] = False
                                processed.append(item)
                            except Exception as exc:
                                self._record_failure(zip_file, source_path, relative_source, exc, failed)
                            self._write_progress_manifest(manifest_path, metadata, processed, failed, write_manifest)

            status = "success" if processed and not failed else "partial" if processed else "error"
            result = {
                "zip": zip_file.name,
                "status": status,
                "media_found": len(extraction.media),
                "media_processed": len(processed),
                "media_resumed": sum(item.get("resumed", False) for item in processed),
                "media_failed": len(failed),
                "parallel_workers": self._effective_parallelism(),
                "nested_zips": len(extraction.nested_zips),
                "ignored_files": len(extraction.ignored_files),
                "max_zip_depth": extraction.max_depth_reached,
                "extracted_files": extraction.extracted_files,
                "extracted_bytes": extraction.extracted_bytes,
                "videos": sorted(processed, key=lambda item: str(item.get("source", ""))),
                "errors": failed,
                "output_folders": sorted({item["output_folder"] for item in processed}),
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

    def _try_resume(self, existing_entry: dict[str, Any] | None, target: str, relative_source: str) -> dict[str, Any] | None:
        if not existing_entry or existing_entry.get("status") != "success" or existing_entry.get("source") != relative_source:
            return None
        folder = normalize_component(str(existing_entry.get("output_folder", "")))
        if not folder:
            return None
        if not self.storage.folder_exists(target, folder):
            return None
        output_folder = self.storage.ensure_folder(target, folder)
        original_folder = self.storage.ensure_folder(output_folder, self.settings.original_transcript_subdir)
        artifacts = (normalize_filename(str(existing_entry.get("video", ""))), normalize_filename(str(existing_entry.get("audio", ""))), normalize_filename(str(existing_entry.get("translated_vtt", ""))))
        original = normalize_filename(str(existing_entry.get("original_transcription", "")))
        if not all(artifacts) or not original:
            return None
        if not all(self.storage.file_exists(output_folder, name) for name in artifacts):
            return None
        if not self.storage.file_exists(original_folder, original):
            return None
        resumed = dict(existing_entry)
        resumed.update({"output_folder": folder, "video": artifacts[0], "audio": artifacts[1], "translated_vtt": artifacts[2], "original_transcription": original, "output_relative_path": f"{folder}/{artifacts[0]}", "source": relative_source})
        return resumed

    def _process_media(self, source_path: Path, extract_root: Path, work_root: Path, target: str, stem: str) -> dict[str, Any]:
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
        for local_path, mime in ((artifacts.mp4_path, "video/mp4"), (artifacts.mp3_path, "audio/mpeg"), (translated_path, "text/vtt")):
            self.storage.upload_file(local_path, output_folder, mime)
        self.storage.upload_file(original_path, original_target, "text/vtt")

        return {
            "source": str(source_path.relative_to(extract_root)),
            "video": artifacts.mp4_path.name,
            "audio": artifacts.mp3_path.name,
            "translated_vtt": translated_path.name,
            "original_transcription": original_path.name,
            "output_folder": stem,
            "output_relative_path": f"{stem}/{artifacts.mp4_path.name}",
            "segments": len(translated),
            "status": "success",
        }

    def _allocate_stem(self, base: str, used: set[str], target: str, source_path: Path, extract_root: Path, work_root: Path) -> str:
        parent = local_storage_paths()["output"] if self.settings.provider.lower() == "local" else work_root
        reserve = (f"_{self.settings.target_lang.lower()}.vtt", "_original.vtt")
        candidate = fit_output_stem(base, parent, reserve_suffixes=reserve)
        if candidate not in used and not self.storage.folder_exists(target, candidate):
            used.add(candidate)
            return candidate
        relative = source_path.relative_to(extract_root).as_posix()
        digest = hashlib.sha256(relative.encode("utf-8")).hexdigest()[:8]
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
