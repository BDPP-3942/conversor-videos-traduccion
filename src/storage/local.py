from __future__ import annotations

import shutil
import time
from pathlib import Path

from config.settings import resolve_project_path
from src.storage.base import StorageFile, StorageProvider
from src.storage.processed_registry import ProcessedRegistry, sha256_file


class LocalStorageProvider(StorageProvider):
    """Proveedor local. La configuración por defecto usa ./storage del proyecto."""

    def __init__(self, retain_sources: bool = True, input_min_age_seconds: int = 60) -> None:
        self.retain_sources = retain_sources
        self.input_min_age_seconds = max(0, input_min_age_seconds)

    @staticmethod
    def _folder(value: str) -> Path:
        path = resolve_project_path(value)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _storage_root(self, location: str) -> Path:
        path = self._folder(location)
        return path

    def list_zip_files(self, location: str) -> list[StorageFile]:
        folder = self._storage_root(location)
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

    def source_fingerprint(self, file: StorageFile) -> dict[str, object]:
        source = Path(file.id).resolve()
        return {
            "sha256": sha256_file(source),
            "size": source.stat().st_size,
        }

    def is_processed(self, file: StorageFile) -> bool:
        fingerprint = self.source_fingerprint(file)
        registry = ProcessedRegistry(self._storage_root("storage/state") / "processed.jsonl")
        return registry.contains_success(file.name, str(fingerprint["sha256"]))

    def finalize_source(
        self,
        file: StorageFile,
        status: str,
        output_folders: list[str] | None = None,
    ) -> None:
        if status != "success" or not self.retain_sources:
            return

        source = Path(file.id).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Source disappeared before archiving: {source}")

        fingerprint = self.source_fingerprint(file)
        archive_root = self._storage_root("storage/archive/sources")
        archive_root.mkdir(parents=True, exist_ok=True)
        short_hash = str(fingerprint["sha256"])[:16]
        archive_name = f"{source.stem}__{short_hash}{source.suffix.lower()}"
        archive_path = archive_root / archive_name

        shutil.copy2(source, archive_path)
        archived_hash = sha256_file(archive_path)
        if archived_hash != fingerprint["sha256"]:
            archive_path.unlink(missing_ok=True)
            raise IOError("Archived source checksum does not match the original")

        registry = ProcessedRegistry(self._storage_root("storage/state") / "processed.jsonl")
        registry.append_success(
            source_name=file.name,
            sha256=str(fingerprint["sha256"]),
            size=int(fingerprint["size"]),
            archive_name=archive_name,
            output_folders=output_folders or [],
        )

        # Eliminar de la bandeja de entrada solo después de validar la copia y registrar el estado.
        source.unlink()
