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

    def rename_output_folder(self, target: str, old_name: str, new_name: str, original_transcript_subdir: str) -> dict[str, str]:
        return {}

    def delete_folder(self, parent: str, name: str) -> None:
        """Delete a complete output folder using provider-native storage operations."""
        wrapped = getattr(self, "wrapped", None)
        if wrapped is not None:
            wrapped.delete_folder(parent, name)
            return
        children = self.list_children(parent)
        folder = next((item for item in children if item.name == name and item.is_directory), None)
        if folder is None:
            return
        class_name = type(self).__name__
        if class_name == "LocalStorageProvider":
            import shutil

            path = Path(folder.id)
            if path.is_dir():
                shutil.rmtree(path)
            return
        if class_name == "GoogleDriveStorageProvider":
            service = getattr(self, "_service", None)
            if service is None:
                raise RuntimeError("Google Drive deletion service is unavailable")
            def trash_tree(folder_id: str) -> None:
                for child in self.list_children(folder_id):
                    if child.is_directory:
                        trash_tree(child.id)
                    service.files().update(fileId=child.id, body={"trashed": True}, fields="id").execute()
            trash_tree(folder.id)
            service.files().update(fileId=folder.id, body={"trashed": True}, fields="id").execute()
            return
        if class_name == "RcloneStorageProvider":
            runner = getattr(self, "_run", None)
            remote = getattr(self, "remote", "")
            if runner is None:
                raise RuntimeError("rclone deletion runner is unavailable")
            runner(["purge", f"{remote}:{name.rstrip('/')}"])
            return
        raise NotImplementedError(f"Storage provider {class_name} does not implement delete_folder")

    def normalize_existing_output_names(self, target: str, original_transcript_subdir: str) -> dict[str, str]:
        return {}

    def source_fingerprint(self, file: StorageFile) -> dict[str, Any]:
        return {"id": file.id, "name": file.name}

    def finalize_source(self, file: StorageFile, status: str, output_folders: list[str] | None = None) -> None:
        return None

    def close(self) -> None:
        return None
