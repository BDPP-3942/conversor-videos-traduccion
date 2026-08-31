from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StorageFile:
    id: str
    name: str
    is_directory: bool = False


class StorageProvider(ABC):
    @abstractmethod
    def list_zip_files(self, location: str) -> list[StorageFile]:
        raise NotImplementedError

    @abstractmethod
    def download_file(self, file: StorageFile, destination: Path) -> None:
        raise NotImplementedError

    @abstractmethod
    def upload_file(self, local_path: Path, location: str, mime_type: str | None = None) -> StorageFile:
        raise NotImplementedError

    @abstractmethod
    def ensure_folder(self, parent: str, name: str) -> str:
        raise NotImplementedError

    def folder_exists(self, parent: str, name: str) -> bool:
        return False

    def file_exists(self, parent: str, name: str) -> bool:
        return False

    def list_children(self, parent: str) -> list[StorageFile]:
        return []

    def rename_output_folder(
        self, target: str, old_name: str, new_name: str, original_transcript_subdir: str
    ) -> dict[str, str]:
        return {}

    def delete_folder(self, parent: str, name: str) -> None:
        """Delete a complete output folder using provider-native storage operations."""
        raise NotImplementedError("This storage provider does not support folder deletion")

    def backup_output_folder(self, target: str, folder: str, backup_name: str, original_transcript_subdir: str) -> bool:
        """Move an existing output folder into a provider-managed regeneration backup."""
        if not self.folder_exists(target, folder):
            return False
        if self.folder_exists(target, backup_name):
            raise FileExistsError(f"Regeneration backup already exists: {backup_name}")
        self.rename_output_folder(target, folder, backup_name, original_transcript_subdir)
        return True

    def restore_output_backup(self, target: str, backup_name: str, folder: str, original_transcript_subdir: str) -> bool:
        """Restore a regeneration backup when the original output path is free."""
        if not self.folder_exists(target, backup_name) or self.folder_exists(target, folder):
            return False
        self.rename_output_folder(target, backup_name, folder, original_transcript_subdir)
        return True

    def delete_output_backup(self, target: str, backup_name: str) -> None:
        """Commit a successful regeneration by deleting its obsolete backup."""
        if self.folder_exists(target, backup_name):
            self.delete_folder(target, backup_name)

    def normalize_existing_output_names(self, target: str, original_transcript_subdir: str) -> dict[str, str]:
        return {}

    def source_fingerprint(self, file: StorageFile) -> dict[str, Any]:
        return {"id": file.id, "name": file.name}

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        return None

    def close(self) -> None:
        return None
