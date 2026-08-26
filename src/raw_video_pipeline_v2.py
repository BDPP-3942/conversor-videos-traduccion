from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from config.settings import AppSettings, local_storage_paths
from src.media_converter import MediaConverter
from src.naming_policy import resolve
from src.storage.base import StorageFile, StorageProvider
from src.stt_engine import STTEngine
from src.translator import TextTranslator
from src.vtt_builder import VTTBuilder

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv"}


class RawVideoPipeline:
    def __init__(self, settings: AppSettings, storage: StorageProvider) -> None:
        self.settings = settings
        self.storage = storage
        self.converter = MediaConverter(settings)
        self.stt = STTEngine(settings)
        self.translator = TextTranslator(settings)

    def run(self, source: str, target: str) -> dict[str, Any]:
        files = [
            file
            for file in self.storage.list_children(source)
            if not file.is_directory and Path(file.name).suffix.lower() in VIDEO_EXTENSIONS
        ]
        results = []
        for source_file in files:
            try:
                results.append(self._process(source_file, target))
            except Exception as exc:
                results.append(
                    {
                        "video": source_file.name,
                        "status": "error",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
        failed = sum(item["status"] == "error" for item in results)
        return {
            "status": "error" if failed and failed == len(results) else "success",
            "videos_found": len(files),
            "videos_processed": sum(item["status"] == "success" for item in results),
            "videos_partial": sum(item["status"] == "partial_translation" for item in results),
            "videos_failed": failed,
            "videos": results,
        }

    def _process(self, source_file: StorageFile, target: str) -> dict[str, Any]:
        metadata = resolve(Path(source_file.name), Path("."))
        with tempfile.TemporaryDirectory(dir=local_storage_paths()["work"]) as temp:
            root = Path(temp)
            input_path = root / source_file.name
            self.storage.download_file(source_file, input_path)
            converted = self.converter.convert(input_path, metadata.output_stem, root / "processed")
            segments = self.stt.transcribe(converted.mp4_path)
            if not segments:
                raise RuntimeError(f"No STT segments generated for {source_file.name}")
            original = root / f"{metadata.output_stem}_original.vtt"
            VTTBuilder.generate_vtt(segments, original)
            translated = self.translator.translate_segments(segments)
            failed = sum(bool(item.get("translation_failed")) for item in translated)
            translated_path = root / f"{metadata.output_stem}_{self.settings.target_lang.lower()}.vtt"
            VTTBuilder.generate_vtt(translated, translated_path)
            output = self.storage.ensure_folder(target, metadata.output_stem)
            original_target = self.storage.ensure_folder(output, self.settings.original_transcript_subdir)
            self.storage.upload_file(converted.mp4_path, output, "video/mp4")
            if converted.secondary_video_path:
                self.storage.upload_file(converted.secondary_video_path, output, "video/webm")
            self.storage.upload_file(translated_path, output, "text/vtt")
            self.storage.upload_file(original, original_target, "text/vtt")
            return {
                "video": source_file.name,
                "status": "partial_translation" if failed else "success",
                "output_folder": metadata.output_stem,
                "segments": len(segments),
                "translation_failed_segments": failed,
                "name_metadata": {
                    "course": metadata.course,
                    "lesson": metadata.lesson,
                    "description": metadata.description,
                    "output_stem": metadata.output_stem,
                },
            }
