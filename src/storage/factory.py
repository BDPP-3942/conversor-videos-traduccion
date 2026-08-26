from __future__ import annotations

from config.settings import AppSettings, resolve_project_path
from src.storage.base import StorageProvider
from src.storage.google_drive import GoogleDriveStorageProvider
from src.storage.local import LocalStorageProvider
from src.storage.rclone import RcloneStorageProvider


def create_storage_provider(provider: str, settings: AppSettings) -> StorageProvider:
    normalized = provider.lower()
    if normalized == "local":
        return LocalStorageProvider(settings.local_retain_sources, settings.local_input_min_age_seconds)
    if normalized in {"google_drive", "gdrive"}:
        provider = GoogleDriveStorageProvider(
            resolve_project_path(settings.google_credentials_file),
            resolve_project_path(settings.google_token_file),
            archive_folder_id=settings.archive_folder_id,
        )
        return provider
    if normalized == "rclone":
        return RcloneStorageProvider(
            resolve_project_path(settings.rclone_binary_file),
            resolve_project_path(settings.rclone_config_file),
            settings.rclone_remote,
        )
    raise ValueError(f"Unsupported storage provider: {provider}")
