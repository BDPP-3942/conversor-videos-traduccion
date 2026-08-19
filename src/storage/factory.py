from __future__ import annotations

from pathlib import Path

from config.settings import AppSettings, resolve_project_path
from src.storage.base import StorageProvider
from src.storage.google_drive import GoogleDriveStorageProvider
from src.storage.local import LocalStorageProvider
from src.storage.rclone import RcloneStorageProvider


def create_storage_provider(provider: str, settings: AppSettings) -> StorageProvider:
    normalized = provider.lower()
    if normalized == "local":
        return LocalStorageProvider(
            settings.local_archive_successful, settings.local_input_min_age_seconds
        )
    if normalized in {"google_drive", "gdrive"}:
        return GoogleDriveStorageProvider(
            resolve_project_path(settings.google_credentials_file),
            resolve_project_path(settings.google_token_file),
        )
    if normalized == "rclone":
        return RcloneStorageProvider(
            resolve_project_path(settings.rclone_config_file),
            settings.rclone_remote,
        )
    raise ValueError(f"Unsupported storage provider: {provider}")
