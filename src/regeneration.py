from __future__ import annotations

import argparse
import json
import logging
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from config.loader import load_settings
from config.settings import ensure_directories, local_storage_paths, resolve_project_path
from src.auth.unattended import check_unattended
from src.cli_run_options import add_regenerate_run_options, apply_shared_run_overrides
from src.runtime_lock import RunLock
from src.storage.factory import create_storage_provider
from src.storage.uri import parse_storage_uri

logger = logging.getLogger(__name__)


class RegenerationError(RuntimeError):
    """Raised when a clean regeneration cannot be completed safely."""


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


def _download_remote_manifest(storage, target: str, zip_name: str) -> Path | None:
    manifest_name = f"{Path(zip_name).stem}.json"
    try:
        candidates = [
            item for item in storage.list_children(target) if item.name == manifest_name and not item.is_directory
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


def _load_existing_entries(storage, target: str, zip_name: str) -> list[dict[str, Any]]:
    path = _manifest_local_path(zip_name)
    manifest = _read_manifest(path)
    if not manifest:
        remote = _download_remote_manifest(storage, target, zip_name)
        if remote:
            manifest = _read_manifest(remote)
    return [entry for entry in manifest.get("entries", []) if isinstance(entry, dict) and entry.get("output_folder")]


def _backup_existing_outputs(
    storage, target: str, entries: list[dict[str, Any]], run_id: str, transcript_subdir: str
) -> list[tuple[str, str]]:
    backups: list[tuple[str, str]] = []
    seen: set[str] = set()
    for entry in entries:
        folder = str(entry.get("output_folder", "")).strip()
        if not folder or folder in seen:
            continue
        seen.add(folder)
        backup = f".regeneration-backup-{run_id}-{folder}"
        if storage.backup_output_folder(target, folder, backup, transcript_subdir):
            backups.append((folder, backup))
    return backups


def _restore_backups(storage, target: str, backups: list[tuple[str, str]], transcript_subdir: str) -> None:
    for original, backup in reversed(backups):
        try:
            storage.restore_output_backup(target, backup, original, transcript_subdir)
        except Exception:
            logger.exception("Could not restore regeneration backup %s", backup)


def _delete_backups(storage, target: str, backups: list[tuple[str, str]]) -> None:
    for _, backup in backups:
        storage.delete_output_backup(target, backup)


def _restore_manifest(storage, target: str, zip_name: str, original: dict[str, Any], remote: bool) -> None:
    if not original:
        return
    path = _manifest_local_path(zip_name)
    path.write_text(json.dumps(original, ensure_ascii=False, indent=2), encoding="utf-8")
    if remote:
        try:
            storage.upload_file(path, target, "application/json")
        except Exception:
            logger.exception("Could not restore manifest for %s", zip_name)


def regenerate(source: str, target: str, settings) -> dict[str, Any]:
    """Regenerate existing results through MediaPipeline and StorageProvider contracts."""
    from src.pipeline import MediaPipeline

    storage = create_storage_provider(settings.provider, settings)
    run_id = uuid.uuid4().hex[:12]
    backups: list[tuple[str, str]] = []
    original_manifests: dict[str, dict[str, Any]] = {}
    remote_manifests: set[str] = set()
    try:
        zips = storage.list_zip_files(source)
        if not zips:
            raise RegenerationError(f"No ZIP sources found in {source!r}")

        for zip_file in zips:
            manifest_path = _manifest_local_path(zip_file.name)
            original_manifests[zip_file.name] = _read_manifest(manifest_path)
            if not original_manifests[zip_file.name]:
                remote = _download_remote_manifest(storage, target, zip_file.name)
                if remote:
                    original_manifests[zip_file.name] = _read_manifest(remote)
                    remote_manifests.add(zip_file.name)
            entries = _load_existing_entries(storage, target, zip_file.name)
            backups.extend(
                _backup_existing_outputs(storage, target, entries, run_id, settings.original_transcript_subdir)
            )

        pipeline = MediaPipeline(settings, storage)
        result = pipeline.run(source, target, force_reprocess=True, finalize_source=False)
        if result.get("status") != "success":
            raise RegenerationError(f"Regeneration did not complete successfully (status={result.get('status')!r})")

        _delete_backups(storage, target, backups)
        return {
            "status": "success",
            "mode": "regenerate_from_zero",
            "source_preserved": True,
            "backup_cleanup": "complete",
            "run_id": run_id,
            "pipeline": result,
        }
    except Exception:
        _restore_backups(storage, target, backups, settings.original_transcript_subdir)
        for zip_name, manifest in original_manifests.items():
            _restore_manifest(storage, target, zip_name, manifest, zip_name in remote_manifests)
        raise
    finally:
        storage.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Explicit REGENERATE FROM ZERO operation for existing video results. "
            "It reuses the normal run configuration contract and forces the common MediaPipeline to reprocess sources."
        )
    )
    parser.add_argument("--config", type=Path, default=resolve_project_path("config/app.toml"), help="Path to the TOML configuration file")
    add_regenerate_run_options(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = load_settings(args.config)
    provider = (args.provider or settings.provider).lower()
    settings = replace(settings, provider=provider)

    from main import _build_locations, configure_logging

    source, target = _build_locations(settings, provider, args.source, args.target)
    settings = apply_shared_run_overrides(settings, args)
    if args.no_name_migration:
        settings = replace(settings, normalize_legacy_names=False)

    parsed_source = parse_storage_uri(source)
    parsed_target = parse_storage_uri(target)
    expected_scheme = {"local": "local", "google_drive": "gdrive", "gdrive": "gdrive", "rclone": "rclone"}[provider]
    if parsed_source.scheme != expected_scheme or parsed_target.scheme != expected_scheme:
        raise SystemExit(f"Provider {provider!r} requires {expected_scheme}:// source and target")

    configure_logging(settings.log_level)
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
