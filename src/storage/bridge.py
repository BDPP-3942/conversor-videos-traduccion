from __future__ import annotations

from pathlib import Path
from typing import Any

from src.storage.base import StorageFile, StorageProvider

class BridgedStorageProvider(StorageProvider):
    """Une origen y destino independientes sin duplicar la lógica del pipeline."""
    def __init__(self, source_provider: StorageProvider, target_provider: StorageProvider, source_location: str, target_location: str) -> None:
        self.source_provider = source_provider
        self.target_provider = target_provider
        self._target_locations = {target_location}
        self._target_folder_ids: set[str] = set()
        self._target_file_ids: set[str] = set()

    def list_zip_files(self, location: str) -> list[StorageFile]: return self.source_provider.list_zip_files(location)

    def download_file(self, file: StorageFile, destination: Path) -> None:
        provider = self.target_provider if file.id in self._target_file_ids else self.source_provider
        provider.download_file(file, destination)

    def upload_file(self, local_path: Path, location: str, mime_type: str | None = None) -> StorageFile:
        result = self.target_provider.upload_file(local_path, location, mime_type)
        self._target_file_ids.add(result.id)
        return result

    def ensure_folder(self, parent: str, name: str) -> str:
        result = self.target_provider.ensure_folder(parent, name)
        self._target_locations.add(result)
        self._target_folder_ids.add(result)
        return result

    def folder_exists(self, parent: str, name: str) -> bool: return self.target_provider.folder_exists(parent, name)
    def file_exists(self, parent: str, name: str) -> bool: return self.target_provider.file_exists(parent, name)

    def list_children(self, parent: str) -> list[StorageFile]:
        if parent in self._target_locations or parent in self._target_folder_ids:
            items = self.target_provider.list_children(parent)
            self._target_file_ids.update(item.id for item in items if not item.is_directory)
            self._target_folder_ids.update(item.id for item in items if item.is_directory)
            return items
        return self.source_provider.list_children(parent)

    def delete_folder(self, parent: str, name: str) -> None: self.target_provider.delete_folder(parent, name)
    def rename_output_folder(self, target: str, old_name: str, new_name: str, original_transcript_subdir: str) -> dict[str, str]: return self.target_provider.rename_output_folder(target, old_name, new_name, original_transcript_subdir)
    def normalize_existing_output_names(self, target: str, original_transcript_subdir: str) -> dict[str, str]: return self.target_provider.normalize_existing_output_names(target, original_transcript_subdir)
    def source_fingerprint(self, file: StorageFile) -> dict[str, Any]: return self.source_provider.source_fingerprint(file)
    def is_processed(self, file: StorageFile) -> bool:
        method = getattr(self.source_provider, 'is_processed', None)
        return bool(method(file)) if method else False

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        self.source_provider.finalize_source(file, status, output_folders)

    def close(self) -> None:
        error: Exception | None = None
        try: self.source_provider.close()
        except Exception as exc: error = exc
        try: self.target_provider.close()
        except Exception as exc:
            if error is None: error = exc
        if error is not None: raise error
