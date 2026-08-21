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
    run.add_argument("--provider", choices=["local", "google_drive", "gdrive", "rclone"], default=None)
    run.add_argument("--mode", choices=["local", "cloud", "rclone"], default=None, help="Execution mode alias: local or cloud (Google Drive)")
    run.add_argument("--source", default=None, help="Source URI. Example: local://storage/input")
    run.add_argument("--target", default=None, help="Target URI. Example: gdrive://FOLDER_ID")
    run.add_argument(
        "--no-retain-sources",
        action="store_true",
        help="Remove successful local source ZIPs instead of retaining them in storage/archive/sources",
    )
    run.add_argument(
        "--no-resume",
        action="store_true",
        help="Disable per-video resume and force normal processing for this run",
    )
    run.add_argument(
        "--no-name-migration",
        action="store_true",
        help="Disable migration of legacy output names for this run",
    )
    run.add_argument("--parallel-videos", type=int, default=None, help="Maximum concurrent local video workers")
    run.add_argument("--translation-batch-size", type=int, default=None, help="Translation batch size")
    run.add_argument("--whisper-beam-size", type=int, default=None, help="Whisper beam size (1 is faster)")
    run.add_argument("--whisper-cpu-threads", type=int, default=None, help="CPU threads per Whisper worker; 0=auto")
    run.add_argument("--no-ffmpeg-copy", action="store_true", help="Force MP4 video re-encoding instead of copy/remux attempt")

    auth = sub.add_parser("auth", help="One-time interactive provider setup")
    auth.add_argument("provider", choices=["google"])

    sub.add_parser("doctor", help="Check local runtime and configuration")
    sub.add_parser("init", help="Create the storage and secrets directories")
    return parser


def _build_locations(settings, provider: str, source: str | None, target: str | None):
    if source and target:
        return source, target
    if provider == "google_drive":
        missing = [name for name, value in (("source_folder_id", settings.source_folder_id), ("target_folder_id", settings.target_folder_id)) if not value]
        if missing:
            raise ValueError("Google Drive requires: " + ", ".join(f"google_drive.{item}" for item in missing))
        return f"gdrive://{settings.source_folder_id}", f"gdrive://{settings.target_folder_id}"
    return settings.source, settings.target


def command_run(args) -> int:
    settings = load_settings(args.config)
    mode = (args.mode or "").lower()
    if mode == "cloud":
        provider = "google_drive"
    elif mode:
        provider = mode
    else:
        provider = (args.provider or settings.provider).lower()
    from dataclasses import replace
    settings = replace(settings, provider=provider)
    source, target = _build_locations(settings, provider, args.source, args.target)
    parsed_source = parse_storage_uri(source)
    parsed_target = parse_storage_uri(target)
    if parsed_source.scheme != parsed_target.scheme:
        raise ValueError("Source and target must use the same storage provider")
    expected_scheme = {
        "local": "local",
        "google_drive": "gdrive",
        "gdrive": "gdrive",
        "rclone": "rclone",
    }[provider]
    if parsed_source.scheme != expected_scheme:
        raise ValueError(
            f"Provider '{provider}' requires {expected_scheme}:// URIs "
            f"(received {parsed_source.scheme}:// and {parsed_target.scheme}://)"
        )
    if provider == "local" and args.no_retain_sources:
        settings = replace(settings, local_retain_sources=False)
    if args.no_resume:
        settings = replace(settings, resume_enabled=False)
    if args.no_name_migration:
        settings = replace(settings, normalize_legacy_names=False)
    if args.parallel_videos is not None:
        settings = replace(settings, max_parallel_videos=max(1, args.parallel_videos))
    if args.translation_batch_size is not None:
        settings = replace(settings, translation_batch_size=max(1, args.translation_batch_size))
    if args.whisper_beam_size is not None:
        settings = replace(settings, whisper_beam_size=max(1, args.whisper_beam_size))
    if args.whisper_cpu_threads is not None:
        settings = replace(settings, whisper_cpu_threads=max(0, args.whisper_cpu_threads))
    if args.no_ffmpeg_copy:
        settings = replace(settings, ffmpeg_avoid_reencode=False)
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
