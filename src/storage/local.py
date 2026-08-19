from __future__ import annotations

import shutil
from pathlib import Path
import time

from src.storage.base import StorageFile, StorageProvider
from config.settings import resolve_project_path


class LocalStorageProvider(StorageProvider):
    """Proveedor local. La configuración por defecto usa ./storage del proyecto."""

    def __init__(self, archive_successful: bool = True, input_min_age_seconds: int = 60) -> None:
        self.archive_successful = archive_successful
        self.input_min_age_seconds = max(0, input_min_age_seconds)

    @staticmethod
    def _folder(value: str) -> Path:
        path = resolve_project_path(value)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def list_zip_files(self, location: str) -> list[StorageFile]:
        folder = self._folder(location)
        return [
            StorageFile(id=str(path), name=path.name)
            for path in sorted(folder.rglob("*.zip"))
            if path.is_file()
            and (time.time() - path.stat().st_mtime) >= self.input_min_age_seconds
        ]

    def download_file(self, file: StorageFile, destination: Path) -> None:
        source = Path(file.id).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Local source not found: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    def upload_file(
        self,
        local_path: Path,
        location: str,
        mime_type: str | None = None,
    ) -> StorageFile:
        del mime_type
        source = local_path.resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Local output not found: {source}")
        target_dir = self._folder(location)
        target = target_dir / source.name
        shutil.copy2(source, target)
        return StorageFile(id=str(target), name=target.name)

    def ensure_folder(self, parent: str, name: str) -> str:
        folder = self._folder(parent) / name
        folder.mkdir(parents=True, exist_ok=True)
        return str(folder)

    def finalize_source(self, file: StorageFile, status: str) -> None:
        if status != "success" or not self.archive_successful:
            return
        source = Path(file.id).resolve()
        storage_root = source.parent
        while storage_root.name != "input" and storage_root.parent != storage_root:
            storage_root = storage_root.parent
        if storage_root.name != "input":
            return
        archive_root = storage_root.parent / "archive"
        relative = source.relative_to(storage_root)
        import datetime as _dt
        destination = archive_root / _dt.datetime.now().strftime("%Y%m%d_%H%M%S") / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
