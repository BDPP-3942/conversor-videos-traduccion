from __future__ import annotations

import argparse
import json
import logging
import shutil
import uuid
from pathlib import Path
from typing import Any

from config.loader import load_settings
from config.settings import ensure_directories, local_storage_paths, resolve_project_path
from src.auth.unattended import check_unattended
from src.runtime_lock import RunLock
from src.storage.base import StorageProvider
from src.storage.factory import create_storage_provider
from src.storage.uri import parse_storage_uri

logger = logging.getLogger(__name__)


class RegenerationError(RuntimeError):
    """Raised when a clean regeneration cannot be completed safely."""


def _delete_folder(storage: StorageProvider, folder: str) -> None:
    """Delete a complete output tree using the provider's native mechanism.

    The existing StorageProvider contract predates destructive output cleanup.
    This compatibility adapter keeps those mechanics outside MediaPipeline until
    delete_folder can be promoted to the public provider contract.
    """
    from src.storage.google_drive import GoogleDriveStorageProvider
    from src.storage.local import LocalStorageProvider
    from src.storage.rclone import RcloneStorageProvider

    if isinstance(storage, LocalStorageProvider):
        path = resolve_project_path(folder)
        if path.exists():
            shutil.rmtree(path)
        return

    if isinstance(storage, GoogleDriveStorageProvider):

        def trash_tree(folder_id: str) -> None:
            for child in storage.list_children(folder_id):
                if child.is_directory:
                    trash_tree(child.id)
                storage._service.files().update(fileId=child.id, body={"trashed": True}, fields="id").execute()

        trash_tree(folder)
        storage._service.files().update(fileId=folder, body={"trashed": True}, fields="id").execute()
        return

    if isinstance(storage, RcloneStorageProvider):
        storage._run(["purge", f"{storage.remote}:{folder.rstrip('/')}"])
        return

    raise RegenerationError(f"Storage provider {type(storage).__name__} does not expose safe recursive deletion")


def _manifest_local_path(zip_name: str) -> Path:
    manifest_dir = local_storage_paths()["manifests"]
    manifest_dir.mkdir(parents=True, exist_ok=True)
    return manifest_dir / f"{Path(zip_name).stem}.json"


def _read_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _download_remote_manifest(storage: StorageProvider, target: str, zip_name: str) -> Path | None:
    manifest_name = f"{Path(zip_name).stem}.json"
    try:
        candidates = [
            item
            for item in storage.list_children(target)
            if item.name == manifest_name and not item.is_directory
        ]
    except Exception:
        logger.exception("Could not inspect remote manifest for %s", zip_name)
        return None
    if not candidates:
        return None
    destination = _manifest_local_path(zip_name)
    try:
        storage.download_file(candidates[0], destination)
    except Exception:
        logger.exception("Could not download remote manifest for %s", zip_name)
        return None
    return destination


def _load_existing_entries(storage: StorageProvider, target: str, zip_name: str) -> list[dict[str, Any]]:
    from src.storage.local import LocalStorageProvider

    path = _manifest_local_path(zip_name)
    local_manifest = _read_manifest(path)
    if not local_manifest and not isinstance(storage, LocalStorageProvider):
        remote = _download_remote_manifest(storage, target, zip_name)
        if remote:
            local_manifest = _read_manifest(remote)
    entries = local_manifest.get("entries", [])
    return [entry for entry in entries if isinstance(entry, dict) and entry.get("output_folder")]


def _backup_existing_outputs(
    storage: StorageProvider,
    target: str,
    entries: list[dict[str, Any]],
    run_id: str,
    original_transcript_subdir: str,
) -> list[tuple[str, str]]:
    backups: list[tuple[str, str]] = []
    seen: set[str] = set()
    for entry in entries:
        folder = str(entry.get("output_folder", "")).strip()
        if not folder or folder in seen:
            continue
        seen.add(folder)
        if not storage.folder_exists(target, folder):
            continue
        backup = f".regeneration-backup-{run_id}-{folder}"
        if storage.folder_exists(target, backup):
            raise RegenerationError(f"Regeneration backup already exists: {backup}")
        storage.rename_output_folder(target, folder, backup, original_transcript_subdir)
        backups.append((folder, backup))
    return backups


def _restore_backups(
    storage: StorageProvider, target: str, backups: list[tuple[str, str]], original_transcript_subdir: str
) -> None:
    for original, backup in reversed(backups):
        try:
            if storage.folder_exists(target, backup) and not storage.folder_exists(target, original):
                storage.rename_output_folder(target, backup, original, original_transcript_subdir)
        except Exception:
            logger.exception("Could not restore regeneration backup %s", backup)


def _cloud_folder_id(storage: StorageProvider, target: str, name: str) -> str:
    from src.storage.google_drive import GoogleDriveStorageProvider

    if not isinstance(storage, GoogleDriveStorageProvider):
        return name
    matches = [item for item in storage.list_children(target) if item.name == name and item.is_directory]
    if not matches:
        raise RegenerationError(f"Regeneration backup folder disappeared: {name}")
    return matches[0].id


def _delete_backups(storage: StorageProvider, target: str, backups: list[tuple[str, str]]) -> None:
    from src.storage.local import LocalStorageProvider

    for _, backup in backups:
        if not storage.folder_exists(target, backup):
            continue
        if isinstance(storage, LocalStorageProvider):
            folder_id = str(resolve_project_path(target) / backup)
        else:
            folder_id = _cloud_folder_id(storage, target, backup)
        _delete_folder(storage, folder_id)


def regenerate(source: str, target: str, settings) -> dict[str, Any]:
    """Regenerate existing results while keeping the original source intact."""
    from src.pipeline import MediaPipeline

    storage = create_storage_provider(settings.provider, settings)
    run_id = uuid.uuid4().hex[:12]
    all_backups: list[tuple[str, str]] = []
    try:
        zips = storage.list_zip_files(source)
        if not zips:
            raise RegenerationError(f"No ZIP sources found in {source!r}")

        for zip_file in zips:
            entries = _load_existing_entries(storage, target, zip_file.name)
            all_backups.extend(
                _backup_existing_outputs(
                    storage,
                    target,
                    entries,
                    run_id,
                    settings.original_transcript_subdir,
                )
            )

        # Do not alter normal resume/idempotency semantics. Regeneration is an
        # explicit orchestration mode that bypasses only the reuse decisions.
        pipeline = MediaPipeline(settings, storage)
        storage.is_processed = lambda file: False  # type: ignore[attr-defined]
        storage.finalize_source = lambda file, status, output_folders=None: None  # type: ignore[method-assign]
        pipeline._try_resume = lambda existing_entry, target, relative_source: None  # type: ignore[method-assign]
        pipeline._find_media_duplicate = lambda source_path, normalized_name, registry: None  # type: ignore[method-assign]

        result = pipeline.run(source, target)
        if result.get("status") != "success":
            raise RegenerationError(
                f"Regeneration did not complete successfully (status={result.get('status')!r}); "
                "previous outputs were restored where possible"
            )

        _delete_backups(storage, target, all_backups)
        return {
            "status": "success",
            "mode": "regenerate_from_zero",
            "source_preserved": True,
            "backup_cleanup": "complete",
            "run_id": run_id,
            "pipeline": result,
        }
    except Exception:
        _restore_backups(storage, target, all_backups, settings.original_transcript_subdir)
        raise
    finally:
        storage.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Explicit REGENERATE FROM ZERO operation for existing video results")
    parser.add_argument("--config", type=Path, default=resolve_project_path("config/app.toml"))
    parser.add_argument("--source", default=None, help="Source storage URI containing ZIP inputs")
    parser.add_argument("--target", default=None, help="Target storage URI containing generated outputs")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings(args.config)
    source = args.source or settings.source
    target = args.target or settings.target
    provider = settings.provider.lower()
    expected_scheme = {"local": "local", "google_drive": "gdrive", "gdrive": "gdrive", "rclone": "rclone"}[provider]
    if parse_storage_uri(source).scheme != expected_scheme or parse_storage_uri(target).scheme != expected_scheme:
        raise SystemExit(f"Provider {provider!r} requires {expected_scheme}:// source and target")
    ensure_directories()
    readiness = check_unattended(
        settings, ensure_rclone_binary=(provider == "rclone" and settings.auto_bootstrap_rclone)
    )
    if not readiness.ready:
        print(json.dumps({"status": "not_ready", "checks": readiness.checks, "errors": readiness.errors}, indent=2))
        return 3
    with RunLock(resolve_project_path(settings.run_lock_file)):
        result = regenerate(parse_storage_uri(source).value, parse_storage_uri(target).value, settings)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
