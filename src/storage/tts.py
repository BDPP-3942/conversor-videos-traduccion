from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from config.settings import AppSettings, local_storage_paths
from src.storage.base import StorageFile, StorageProvider
from src.subtitle_repair import repair_output_subtitles
from src.tts_pipeline import TTSProviderError, generate_tts_media

logger = logging.getLogger(__name__)


class TTSAwareStorageProvider(StorageProvider):
    """Storage decorator that adds TTS without creating a second pipeline."""

    def __init__(self, wrapped: StorageProvider, settings: AppSettings) -> None:
        self.wrapped = wrapped
        self.settings = settings
        self._output_folders: set[tuple[str, str, str]] = set()

    def list_zip_files(self, location: str) -> list[StorageFile]:
        return self.wrapped.list_zip_files(location)

    def download_file(self, file: StorageFile, destination: Path) -> None:
        self.wrapped.download_file(file, destination)

    def upload_file(self, local_path: Path, location: str, mime_type: str | None = None) -> StorageFile:
        return self.wrapped.upload_file(local_path, location, mime_type)

    def ensure_folder(self, parent: str, name: str) -> str:
        result = self.wrapped.ensure_folder(parent, name)
        if self.settings.tts_enabled:
            self._output_folders.add((parent, result, name))
        return result

    def folder_exists(self, parent: str, name: str) -> bool:
        return self.wrapped.folder_exists(parent, name)

    def file_exists(self, parent: str, name: str) -> bool:
        return self.wrapped.file_exists(parent, name)

    def list_children(self, parent: str) -> list[StorageFile]:
        return self.wrapped.list_children(parent)

    def rename_output_folder(
        self, target: str, old_name: str, new_name: str, original_transcript_subdir: str
    ) -> dict[str, str]:
        return self.wrapped.rename_output_folder(target, old_name, new_name, original_transcript_subdir)

    def normalize_existing_output_names(self, target: str, original_transcript_subdir: str) -> dict[str, str]:
        return self.wrapped.normalize_existing_output_names(target, original_transcript_subdir)

    def source_fingerprint(self, file: StorageFile) -> dict[str, Any]:
        return self.wrapped.source_fingerprint(file)

    def is_processed(self, file: StorageFile) -> bool:
        method = getattr(self.wrapped, "is_processed", None)
        return bool(method(file)) if method else False

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        if self.settings.tts_enabled and status == "success":
            try:
                self._process_pending_folders()
            except Exception:
                logger.exception("TTS failed before source finalization")
                if self.settings.tts_required:
                    raise
        self.wrapped.finalize_source(file, status, output_folders)

    def close(self) -> None:
        try:
            if self.settings.tts_enabled:
                self._process_pending_folders()
        finally:
            self.wrapped.close()

    def _process_pending_folders(self) -> None:
        for target, folder, folder_name in sorted(self._output_folders):
            self._process_folder(target, folder, folder_name)

    def _process_folder(self, target: str, folder: str, folder_name: str) -> None:
        repair_result = repair_output_subtitles(self.wrapped, self.settings, folder)
        if repair_result.get("status") == "repaired":
            logger.info(
                "Subtitle repair completed before TTS for %s: original=%s translated=%s",
                folder_name,
                repair_result.get("original_repaired"),
                repair_result.get("translated_repaired"),
            )

        children = self.wrapped.list_children(folder)
        files = {child.name: child for child in children if not child.is_directory}
        vtt = next((item for item in files.values() if _is_output_vtt_name(item.name)), None)
        video = next(
            (item for item in files.values() if item.name.lower().endswith(".mp4") and "_tts" not in item.name.lower()),
            None,
        )
        webm = next(
            (
                item
                for item in files.values()
                if item.name.lower().endswith(".webm") and "_tts" not in item.name.lower()
            ),
            None,
        )
        if not vtt or not video:
            logger.warning("Skipping TTS for %s: reusable video or translated VTT is missing", folder_name)
            return

        stem = Path(video.name).stem
        expected_mp4 = f"{stem}_tts.mp4"
        expected_webm = f"{stem}_tts.webm"
        webm_required = self.settings.tts_generate_webm and self.settings.generate_webm
        if self.wrapped.file_exists(folder, expected_mp4) and (
            not webm_required or self.wrapped.file_exists(folder, expected_webm)
        ):
            self._update_manifest(target, folder_name, expected_mp4, expected_webm if webm_required else "")
            return

        with tempfile.TemporaryDirectory(prefix=f"tts_{stem}_") as temp_dir:
            root = Path(temp_dir)
            video_path = root / video.name
            vtt_path = root / vtt.name
            webm_path = root / webm.name if webm else None
            self.wrapped.download_file(video, video_path)
            self.wrapped.download_file(vtt, vtt_path)
            if webm:
                self.wrapped.download_file(webm, webm_path)
            try:
                result = generate_tts_media(
                    video_path,
                    vtt_path,
                    root,
                    stem,
                    self.settings,
                    webm_video_path=webm_path,
                )
                self.wrapped.upload_file(result.mp4_path, folder, "video/mp4")
                if result.webm_path is not None:
                    self.wrapped.upload_file(result.webm_path, folder, "video/webm")
                self.wrapped.upload_file(result.audio_path, folder, "audio/wav")
                self._update_manifest(
                    target,
                    folder_name,
                    result.mp4_path.name,
                    result.webm_path.name if result.webm_path else "",
                    cue_count=result.cue_count,
                    adjusted_cues=result.adjusted_cues,
                )
            except (TTSProviderError, RuntimeError, ValueError, OSError) as exc:
                logger.error("TTS failed for output folder %s: %s", folder_name, exc)
                self._update_manifest_status(target, folder_name, "failed", str(exc))
                if self.settings.tts_required:
                    raise

    def _update_manifest(
        self,
        target: str,
        folder_name: str,
        mp4_name: str,
        webm_name: str,
        *,
        cue_count: int | None = None,
        adjusted_cues: int | None = None,
    ) -> None:
        self._update_manifest_status(
            target,
            folder_name,
            "completed",
            "",
            mp4_name=mp4_name,
            webm_name=webm_name,
            cue_count=cue_count,
            adjusted_cues=adjusted_cues,
        )

    def _update_manifest_status(
        self,
        target: str,
        folder_name: str,
        status: str,
        error: str,
        *,
        mp4_name: str = "",
        webm_name: str = "",
        cue_count: int | None = None,
        adjusted_cues: int | None = None,
    ) -> None:
        manifest_dir = local_storage_paths()["manifests"]
        if not manifest_dir.is_dir():
            return
        from src.manifest import read_manifest, write_manifest

        for manifest_path in manifest_dir.glob("*.json"):
            data = read_manifest(manifest_path)
            changed = False
            for entry in data.get("entries", []):
                if not isinstance(entry, dict) or str(entry.get("output_folder", "")) != folder_name:
                    continue
                for key, value in (("tts_mp4", mp4_name), ("tts_webm", webm_name)):
                    if value and entry.get(key) != value:
                        entry[key] = value
                        changed = True
                for key, value in (("tts_cue_count", cue_count), ("tts_adjusted_cues", adjusted_cues)):
                    if value is not None and entry.get(key) != value:
                        entry[key] = value
                        changed = True
                if entry.get("tts_status") != status:
                    entry["tts_status"] = status
                    changed = True
                if error and entry.get("tts_error") != error:
                    entry["tts_error"] = error
                    changed = True
            if changed:
                write_manifest(manifest_path, data.get("entries", []), metadata=data.get("metadata", {}))
                try:
                    self.wrapped.upload_file(manifest_path, target, "application/json")
                except (OSError, RuntimeError) as exc:
                    logger.warning("Could not upload updated TTS manifest %s: %s", manifest_path, exc)


def _is_output_vtt_name(name: str) -> bool:
    return name.lower().endswith(".vtt") and not name.lower().endswith("_original.vtt")
