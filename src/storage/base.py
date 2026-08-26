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
    def upload_file(
        self,
        local_path: Path,
        location: str,
        mime_type: str | None = None,
    ) -> StorageFile:
        raise NotImplementedError

    @abstractmethod
    def ensure_folder(self, parent: str, name: str) -> str:
        raise NotImplementedError

    def folder_exists(self, parent: str, name: str) -> bool:
        return False

    def file_exists(self, parent: str, name: str) -> bool:
        """Return whether a file exists below a storage folder."""
        return False

    def list_children(self, parent: str) -> list[StorageFile]:
        """List direct child files/folders using the provider-native identifiers."""
        return []

    def rename_output_folder(
        self, target: str, old_name: str, new_name: str, original_transcript_subdir: str
    ) -> dict[str, str]:
        """Rename an already processed output folder and its generated artifact stems."""
        return {}

    def normalize_existing_output_names(self, target: str, original_transcript_subdir: str) -> dict[str, str]:
        """Best-effort migration hook for output names created by older versions."""
        return {}

    def source_fingerprint(self, file: StorageFile) -> dict[str, Any]:
        """Optional source identity used to make resume decisions safer."""
        return {"id": file.id, "name": file.name}

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        """Hook opcional para retirar fuentes procesadas del buzón de entrada."""
        return None

    def close(self) -> None:
        """Hook opcional para liberar recursos del proveedor."""
        return None
