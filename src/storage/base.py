from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


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

    def finalize_source(
        self, file: StorageFile, status: str, output_folders: list[str] | None = None
    ) -> None:
        """Hook opcional para retirar fuentes procesadas del buzón de entrada."""

    def close(self) -> None:
        pass
