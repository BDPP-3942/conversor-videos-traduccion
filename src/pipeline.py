from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from config.settings import AppSettings, local_storage_paths
from src.storage.base import StorageFile, StorageProvider
from src.storage.uri import parse_storage_uri

logger = logging.getLogger(__name__)


class MediaPipeline:
    def __init__(self, settings: AppSettings, storage: StorageProvider) -> None:
        self.settings = settings
        self.storage = storage
        from src.extractor import ZipExtractor
        from src.media_converter import MediaConverter
        from src.stt_engine import STTEngine
        from src.translator import TextTranslator

        self.extractor = ZipExtractor(
            settings.max_zip_depth,
            settings.max_extracted_files,
            settings.max_extracted_size_bytes,
        )
        self.media_converter = MediaConverter(settings)
        self.stt_engine = STTEngine(settings)
        self.translator = TextTranslator(settings)

    def run(self, source: str, target: str) -> dict[str, Any]:
        zips = self.storage.list_zip_files(source)
        if not zips:
            return {"status": "success", "message": "No ZIP files found", "zips_found": 0}

        results = []
        for zip_file in zips:
            try:
                if hasattr(self.storage, "is_processed") and self.storage.is_processed(zip_file):
                    result = {
                        "zip": zip_file.name,
                        "status": "skipped",
                        "reason": "same source name and SHA-256 already processed",
                    }
                else:
                    result = self._process_zip(zip_file, target)
                    if result["status"] == "success":
                        self.storage.finalize_source(
                            zip_file,
                            "success",
                            result.get("output_folders", []),
                        )
            except Exception as exc:
                logger.exception("ZIP processing failed: %s", zip_file.name)
                result = {
                    "zip": zip_file.name,
                    "status": "error",
                    "errors": [{
                        "source": zip_file.name,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }],
                }
            results.append(result)

        failed = sum(item["status"] == "error" for item in results)
        partial = sum(item["status"] == "partial" for item in results)
        processed = sum(item["status"] in {"success", "partial", "error"} for item in results)
        status = "error" if failed and not any(item["status"] == "success" for item in results) else "partial" if failed or partial else "success"
        return {
            "status": status,
            "zips_found": len(zips),
            "zips_processed": processed,
            "zips_skipped": sum(item["status"] == "skipped" for item in results),
            "zips_failed": failed,
            "zips_partial": partial,
            "zips": results,
        }

    def _process_zip(self, zip_file: StorageFile, target: str) -> dict[str, Any]:
        work_base = local_storage_paths()["work"]
        work_base.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix=f"{Path(zip_file.name).stem}_", dir=work_base) as temporary_dir:
            work_root = Path(temporary_dir)
            archive_target = work_root / Path(zip_file.name).name
            self.storage.download_file(zip_file, archive_target)
            extract_root = work_root / "extracted"
            extraction = self.extractor.extract_zip(archive_target, extract_root)
            used_stems: set[str] = set()
            processed: list[dict[str, Any]] = []
            failed: list[dict[str, Any]] = []

            for source_path in extraction.media:
                try:
                    processed.append(
                        self._process_media(
                            source_path,
                            extract_root,
                            work_root,
                            target,
                            used_stems,
                        )
                    )
                except Exception as exc:
                    logger.exception("Media processing failed: %s", source_path.name)
                    failure = {
                        "source": str(source_path.relative_to(extract_root)),
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                    failed.append(failure)
                    self._write_failure(zip_file.name, source_path.name, failure)

            status = "success" if processed and not failed else "partial" if processed else "error"
            result = {
                "zip": zip_file.name,
                "status": status,
                "media_found": len(extraction.media),
                "media_processed": len(processed),
                "media_failed": len(failed),
                "nested_zips": len(extraction.nested_zips),
                "ignored_files": len(extraction.ignored_files),
                "max_zip_depth": extraction.max_depth_reached,
                "extracted_files": extraction.extracted_files,
                "extracted_bytes": extraction.extracted_bytes,
                "videos": processed,
                "errors": failed,
                "output_folders": sorted({item["output_folder"] for item in processed}),
            }

            manifest = local_storage_paths()["manifests"] / f"{Path(zip_file.name).stem}.json"
            from src.manifest import write_manifest
            write_manifest(manifest, result["videos"] + result["errors"])
            if self.settings.provider.lower() in {"google_drive", "gdrive"} and processed:
                self.storage.upload_file(manifest, target, "application/json")

            return result

    def _process_media(
        self,
        source_path: Path,
        extract_root: Path,
        work_root: Path,
        target: str,
        used_stems: set[str],
    ) -> dict[str, Any]:
        from src.file_naming import FileNameFormatter
        metadata = FileNameFormatter.resolve_source_metadata(source_path, extract_root)
        stem = self._allocate_stem(metadata.output_stem, used_stems)

        processed_dir = work_root / "processed"
        artifacts = self.media_converter.convert(source_path, stem, processed_dir)
        segments = self.stt_engine.transcribe(artifacts.mp4_path)
        if not segments:
            raise RuntimeError(f"No STT segments generated for {source_path.name}")

        transcription_dir = work_root / "transcriptions_original"
        transcription_dir.mkdir(parents=True, exist_ok=True)
        original_path = transcription_dir / f"{stem}_original.vtt"

        from src.vtt_builder import VTTBuilder
        VTTBuilder.generate_vtt(segments, original_path)

        translated = self.translator.translate_segments(segments)
        translated_path = work_root / f"{stem}_{self.settings.target_lang.lower()}.vtt"
        VTTBuilder.generate_vtt(translated, translated_path)

        output_folder = self.storage.ensure_folder(target, stem)
        original_target = self.storage.ensure_folder(output_folder, self.settings.original_transcript_subdir)

        for local_path, mime in (
            (artifacts.mp4_path, "video/mp4"),
            (artifacts.mp3_path, "audio/mpeg"),
            (translated_path, "text/vtt"),
        ):
            self.storage.upload_file(local_path, output_folder, mime)

        self.storage.upload_file(original_path, original_target, "text/vtt")

        return {
            "source": str(source_path.relative_to(extract_root)),
            "course": metadata.course,
            "lesson": metadata.lesson,
            "description": metadata.description,
            "confidence": metadata.confidence,
            "review_required": metadata.review_required,
            "review_reason": metadata.review_reason,
            "video": artifacts.mp4_path.name,
            "audio": artifacts.mp3_path.name,
            "translated_vtt": translated_path.name,
            "original_transcription": original_path.name,
            "output_folder": stem,
            "output_relative_path": f"{stem}/{artifacts.mp4_path.name}",
            "segments": len(translated),
            "status": "success",
        }

    def _original_target(self, target: str) -> str:
        # Compatibilidad con integraciones anteriores. El flujo actual publica las
        # transcripciones dentro de output/<video>/original_transcriptions.
        location = parse_storage_uri(target)
        if location.scheme == "local":
            return str(local_storage_paths()["output"])
        return location.value

    @staticmethod
    def _allocate_stem(base: str, used: set[str]) -> str:
        if base not in used:
            used.add(base)
            return base
        index = 2
        while f"{base}__dup{index:02d}" in used:
            index += 1
        unique = f"{base}__dup{index:02d}"
        used.add(unique)
        return unique

    @staticmethod
    def _write_failure(zip_name: str, media_name: str, failure: dict[str, Any]) -> None:
        failure_dir = local_storage_paths()["failures"]
        failure_dir.mkdir(parents=True, exist_ok=True)
        failure_path = failure_dir / f"{Path(zip_name).stem}_{Path(media_name).stem}.json"
        from src.manifest import write_manifest
        write_manifest(failure_path, [failure])

    def cleanup(self) -> None:
        return
