from __future__ import annotations

import argparse
import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config.loader import load_settings
from config.settings import BASE_DIR, ensure_directories, resolve_project_path
from src.storage.factory import create_storage_provider
from src.storage.google_drive import GoogleDriveStorageProvider
from src.ffmpeg_resolver import FFmpegResolver
from src.storage.uri import parse_storage_uri

logger = logging.getLogger(__name__)


def configure_logging(log_level: str) -> None:
    log_dir = BASE_DIR / "storage" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                log_dir / "pipeline.log",
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            ),
        ],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Video/audio STT + translation pipeline")
    parser.add_argument("--config", type=Path, default=BASE_DIR / "config" / "app.toml")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run one processing batch")
    run.add_argument("--provider", choices=["local", "google_drive", "rclone"], default=None)
    run.add_argument("--source", default=None, help="Source URI. Example: local://storage/input")
    run.add_argument("--target", default=None, help="Target URI. Example: gdrive://FOLDER_ID")
    run.add_argument(
        "--no-retain-sources",
        action="store_true",
        help="Remove successful local source ZIPs instead of retaining them in storage/archive/sources",
    )

    auth = sub.add_parser("auth", help="One-time interactive provider setup")
    auth.add_argument("provider", choices=["google"])

    sub.add_parser("doctor", help="Check local runtime and configuration")
    sub.add_parser("init", help="Create the storage and secrets directories")
    return parser


def _build_locations(settings, provider: str, source: str | None, target: str | None):
    if source and target:
        return source, target
    if provider == "google_drive":
        if not settings.source_folder_id or not settings.target_folder_id:
            raise ValueError(
                "Google Drive requires google_drive.source_folder_id and "
                "google_drive.target_folder_id in config/app.toml"
            )
        return f"gdrive://{settings.source_folder_id}", f"gdrive://{settings.target_folder_id}"
    return settings.source, settings.target


def command_run(args) -> int:
    settings = load_settings(args.config)
    provider = (args.provider or settings.provider).lower()
    from dataclasses import replace
    settings = replace(settings, provider=provider)
    source, target = _build_locations(settings, provider, args.source, args.target)
    parsed_source = parse_storage_uri(source)
    parsed_target = parse_storage_uri(target)
    if parsed_source.scheme != parsed_target.scheme:
        raise ValueError("Source and target must use the same storage provider")
    if provider == "local" and args.no_retain_sources:
        settings = replace(settings, local_retain_sources=False)
    configure_logging(settings.log_level)
    from src.pipeline import MediaPipeline
    storage = create_storage_provider(provider, settings)
    pipeline = MediaPipeline(settings, storage)
    try:
        result = pipeline.run(parsed_source.value, parsed_target.value)
    finally:
        storage.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return {"success": 0, "partial": 2, "error": 1}.get(result["status"], 1)


def command_auth(args) -> int:
    settings = load_settings(args.config)
    if args.provider != "google":
        return 2
    configure_logging("INFO")
    provider = GoogleDriveStorageProvider(
        resolve_project_path(settings.google_credentials_file),
        resolve_project_path(settings.google_token_file),
        allow_interactive_auth=True,
    )
    provider.close()
    print("Google Drive authorization completed. Future 'run' executions are unattended.")
    return 0


def command_doctor(args) -> int:
    settings = load_settings(args.config)
    ensure_directories()
    checks = {}
    ffmpeg_check = FFmpegResolver.doctor(settings)
    checks["ffmpeg"] = ffmpeg_check["available"]
    checks["ffmpeg_path"] = ffmpeg_check.get("path", "")
    if "error" in ffmpeg_check:
        checks["ffmpeg_error"] = ffmpeg_check["error"]
    checks["config"] = Path(args.config).is_file()
    checks["local_input"] = (BASE_DIR / "storage" / "input").is_dir()
    checks["local_output"] = (BASE_DIR / "storage" / "output").is_dir()
    checks["python"] = sys.version_info >= (3, 11)
    print(json.dumps(checks, indent=2))
    return 0 if all(checks.values()) else 1


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "init":
        ensure_directories()
        print(f"Storage initialized under: {BASE_DIR / 'storage'}")
        return 0
    try:
        ensure_directories()
        if args.command == "run":
            return command_run(args)
        if args.command == "auth":
            return command_auth(args)
        if args.command == "doctor":
            return command_doctor(args)
        return 2
    except Exception as exc:
        logging.getLogger(__name__).exception("Command failed")
        print(
            json.dumps(
                {"status": "error", "error_type": type(exc).__name__, "error": str(exc)},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
