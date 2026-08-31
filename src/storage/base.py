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
        """Delete a complete output folder using the provider's native operations."""
        raise NotImplementedError(f"{type(self).__name__} does not implement delete_folder")

    def normalize_existing_output_names(self, target: str, original_transcript_subdir: str) -> dict[str, str]:
        return {}

    def source_fingerprint(self, file: StorageFile) -> dict[str, Any]:
        return {"id": file.id, "name": file.name}

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        return None

    def close(self) -> None:
        return None
