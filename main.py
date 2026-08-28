# ruff: noqa: E501
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import replace
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from config.loader import load_settings
from config.settings import BASE_DIR, ensure_directories, resolve_project_path
from src.auth.google_oauth import GoogleOAuthManager
from src.auth.rclone_manager import RcloneManager
from src.auth.unattended import check_unattended
from src.ffmpeg_resolver import FFmpegResolver
from src.providers.registry import ProviderRegistry
from src.providers.runtime import clear_runtime, load_runtime, save_runtime
from src.runtime_lock import RunLock
from src.storage.factory import create_storage_provider
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
            RotatingFileHandler(log_dir / "pipeline.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"),
        ],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unattended video/audio STT + translation pipeline")
    parser.add_argument("--config", type=Path, default=BASE_DIR / "config" / "app.toml")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run one unattended processing batch using the saved active profile")
    run.add_argument("--scheduled", action="store_true", help="Scheduled-task mode: never opens a browser or asks for input")
    run.add_argument("--dry-run", action="store_true", help="Validate readiness without processing files")
    run.add_argument("--provider", choices=["local", "google_drive", "gdrive", "rclone"], default=None)
    run.add_argument("--source", default=None)
    run.add_argument("--target", default=None)
    run.add_argument("--no-retain-sources", action="store_true")
    run.add_argument("--no-resume", action="store_true")
    run.add_argument("--no-name-migration", action="store_true")
    run.add_argument("--parallel-videos", type=int, default=None)
    run.add_argument("--translation-batch-size", type=int, default=None)
    run.add_argument("--whisper-beam-size", type=int, default=None)
    run.add_argument("--whisper-cpu-threads", type=int, default=None)
    run.add_argument("--no-ffmpeg-copy", action="store_true")
    webm_group = run.add_mutually_exclusive_group()
    webm_group.add_argument("--generate-webm", dest="generate_webm", action="store_true", help="Generate the secondary WebM output")
    webm_group.add_argument("--no-webm", dest="generate_webm", action="store_false", help="Do not generate the secondary WebM output")
    run.set_defaults(generate_webm=None)

    duplicates = sub.add_parser("duplicates", help="Inspect and manage duplicate local output folders")
    duplicates.add_argument("--target", type=Path, default=BASE_DIR / "storage" / "output", help="Local output directory")
    duplicate_sub = duplicates.add_subparsers(dest="duplicates_command", required=True)
    duplicate_sub.add_parser("scan", help="Detect duplicate output groups without modifying results")
    duplicate_sub.add_parser("analyze", help="Analyze duplicate groups and persist the deletion plan")
    delete_duplicates = duplicate_sub.add_parser("delete", help="Delete only duplicates present in the persisted analysis plan")
    delete_duplicates.add_argument("--dry-run", action="store_true", help="Show exactly what would be deleted without deleting anything")

    auth = sub.add_parser("auth", help="One-time interactive authentication")
    auth.add_argument("provider", choices=["google"])
    auth.add_argument("--profile", default="default")
    provider = sub.add_parser("provider", help="Configure and switch persistent provider profiles")
    provider_sub = provider.add_subparsers(dest="provider_command", required=True)
    provider_sub.add_parser("bootstrap", help="Install the managed rclone binary")
    provider_sub.add_parser("list", help="List configured provider profiles and active runtime")
    verify = provider_sub.add_parser("verify", help="Run a read-only cloud credential check")
    verify.add_argument("provider", choices=["google_drive", "rclone"])
    verify.add_argument("--profile", default="default")
    verify.add_argument("--location", default="", help="rclone folder used for the read-only health check")
    update = provider_sub.add_parser("update-rclone", help="Update managed rclone binary explicitly")
    update.add_argument("--force", action="store_true", help="Run the update even when auto-update is disabled")
    setup_google = provider_sub.add_parser("setup-google", help="One-time Google Drive setup: OAuth + folders + active profile")
    setup_google.add_argument("--profile", default="default")
    setup_google.add_argument("--source-folder-id", required=True)
    setup_google.add_argument("--target-folder-id", required=True)
    setup_google.add_argument("--archive-folder-id", default="")
    auth_rclone = provider_sub.add_parser("auth-rclone", help="One-time rclone remote configuration")
    auth_rclone.add_argument("name")
    auth_rclone.add_argument("backend")
    auth_rclone.add_argument("options", nargs="*")
    auth_rclone.add_argument("--non-interactive", action="store_true")
    setup_rclone = provider_sub.add_parser("setup-rclone", help="One-time rclone setup + active source/target")
    setup_rclone.add_argument("name")
    setup_rclone.add_argument("backend")
    setup_rclone.add_argument("--source", required=True, help="Remote folder path, e.g. input")
    setup_rclone.add_argument("--target", required=True, help="Remote folder path, e.g. output")
    setup_rclone.add_argument("--option", action="append", default=[], help="rclone option as key=value; repeatable")
    use = provider_sub.add_parser("use", help="Select the active provider/profile")
    use.add_argument("provider", choices=["local", "google_drive", "rclone"])
    use.add_argument("--profile", default="default")
    use.add_argument("--source", required=True)
    use.add_argument("--target", required=True)
    use.add_argument("--archive", default="")
    remove = provider_sub.add_parser("remove", help="Remove an unused cloud profile")
    remove.add_argument("provider", choices=["google_drive", "rclone"])
    remove.add_argument("name")
    provider_sub.add_parser("clear", help="Return to config/app.toml as active provider")

    reprocess = sub.add_parser("reprocess-subtitles", help="Reprocess STT and/or translation inside an existing output folder without regenerating media")
    mode = reprocess.add_mutually_exclusive_group()
    mode.add_argument("--stt-only", action="store_true", help="Regenerate only the original transcription")
    mode.add_argument("--translate-only", action="store_true", help="Regenerate only the translated VTT")
    reprocess.add_argument("--output-folder", default=None)
    reprocess.add_argument("--all", dest="reprocess_all", action="store_true")
    reprocess.add_argument("--video", dest="video_name", default=None)
    reprocess.add_argument("--source", default=None)
    reprocess.add_argument("--scheduled", action="store_true")
    reprocess.add_argument("--provider", choices=["local", "google_drive", "gdrive", "rclone"], default=None)
    reprocess.add_argument("--target", default=None)
    sub.add_parser("prefetch-whisper", help="Download/initialize the automatically selected Whisper model")
    sub.add_parser("doctor", help="Check interactive and unattended runtime readiness")
    sub.add_parser("init", help="Create runtime directories")
    return parser


def _build_locations(settings, provider: str, source: str | None, target: str | None):
    if source and target:
        return source, target
    return settings.source, settings.target


def _run_automatic_deduplication(settings, target: str) -> dict[str, Any] | None:
    if not getattr(settings, "automatic_output_deduplication", True) or settings.provider.lower() != "local":
        return None
    from src.output_deduplicator import OutputDeduplicator
    target_path = resolve_project_path(target.removeprefix("local://"))
    deduplicator = OutputDeduplicator(target_path)
    deduplicator.scan_and_persist()
    plan = deduplicator.analyze_and_persist()
    results = deduplicator.delete()
    return {"plan": plan, "results": results}


def _run_output_postprocessing(settings, storage, target: str) -> dict[str, Any] | None:
    if not settings.tts_enabled:
        return None
    from src.output_postprocessor import OutputPostProcessor
    return OutputPostProcessor(settings, storage).process_target(target)


def command_run(args) -> int:
    settings = load_settings(args.config)
    provider = (args.provider or settings.provider).lower()
    if args.scheduled and any(value is not None for value in (args.provider, args.source, args.target)):
        raise ValueError("Scheduled mode must use the saved active provider configuration")
    settings = replace(settings, provider=provider)
    source, target = _build_locations(settings, provider, args.source, args.target)
    parsed_source = parse_storage_uri(source)
    parsed_target = parse_storage_uri(target)
    expected_scheme = {"local": "local", "google_drive": "gdrive", "gdrive": "gdrive", "rclone": "rclone"}[provider]
    if parsed_source.scheme != expected_scheme or parsed_target.scheme != expected_scheme:
        raise ValueError(f"Provider {provider!r} requires {expected_scheme}:// source and target")
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
    if args.generate_webm is not None:
        settings = replace(settings, generate_webm=args.generate_webm)
    configure_logging(settings.log_level)
    if provider == "rclone" and settings.auto_update_rclone:
        try:
            RcloneManager(resolve_project_path(settings.rclone_binary_file), resolve_project_path(settings.rclone_config_file)).self_update()
        except Exception as exc:
            logger.warning("Automatic rclone update skipped: %s", exc)
    readiness = check_unattended(settings, ensure_rclone_binary=(provider == "rclone" and settings.auto_bootstrap_rclone))
    if not readiness.ready:
        print(json.dumps({"status": "not_ready", "provider": provider, "checks": readiness.checks, "errors": readiness.errors}, ensure_ascii=False, indent=2)); return 3
    if args.dry_run:
        print(json.dumps({"status": "ready", "provider": provider, "checks": readiness.checks}, ensure_ascii=False, indent=2)); return 0
    from src.pipeline import MediaPipeline
    with RunLock(resolve_project_path(settings.run_lock_file)):
        storage = create_storage_provider(provider, settings)
        try:
            result = MediaPipeline(settings, storage).run(parsed_source.value, parsed_target.value)
            postprocessing = _run_output_postprocessing(settings, storage, parsed_target.value)
            if postprocessing is not None:
                result["tts_postprocessing"] = postprocessing
                if postprocessing.get("failed", 0):
                    result["status"] = "error" if settings.tts_required else "partial"
            automatic_deduplication = _run_automatic_deduplication(settings, parsed_target.value)
            if automatic_deduplication is not None:
                result["automatic_deduplication"] = automatic_deduplication
                if any(item.get("status") == "skipped" for item in automatic_deduplication["results"]):
                    result["status"] = "partial"
        finally:
            storage.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return {"success": 0, "partial": 2, "error": 1}.get(result["status"], 1)


def command_duplicates(args) -> int:
    settings = load_settings(args.config)
    configure_logging(settings.log_level)
    from src.output_deduplicator import OutputDeduplicator
    deduplicator = OutputDeduplicator(args.target)
    if args.duplicates_command == "scan":
        payload = deduplicator.scan_and_persist(); print(json.dumps(payload, ensure_ascii=False, indent=2)); return 0
    if args.duplicates_command == "analyze":
        payload = deduplicator.analyze_and_persist(); print(json.dumps(payload, ensure_ascii=False, indent=2)); return 0
    results = deduplicator.delete(dry_run=args.dry_run); print(json.dumps({"status": "success", "dry_run": args.dry_run, "results": results}, ensure_ascii=False, indent=2)); return 0


def command_auth(args) -> int:
    settings = load_settings(args.config)
    profile_dir = resolve_project_path(settings.provider_profile_dir) / "google" / args.profile
    manager = GoogleOAuthManager(profile_dir / "credentials.json", profile_dir / "token.json")
    credentials = manager.authorize(open_browser=True)
    print(json.dumps({"provider": "google_drive", "profile": args.profile, "authorized": bool(credentials.valid or credentials.refresh_token), "token_file": str(manager.token_file)}, ensure_ascii=False, indent=2)); return 0


def command_provider(args) -> int:
    settings = load_settings(args.config)
    registry = ProviderRegistry(settings)
    if args.provider_command == "bootstrap":
        path = registry.rclone.ensure_binary(); print(json.dumps({"status": "success", "rclone": str(path), "version": registry.rclone.version()}, indent=2)); return 0
    if args.provider_command == "list":
        result = registry.list_profiles(); result["runtime"] = load_runtime().get("active", {}); print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    if args.provider_command == "verify":
        if args.provider == "google_drive":
            profile_dir = resolve_project_path(settings.provider_profile_dir) / "google" / args.profile
            manager = GoogleOAuthManager(profile_dir / "credentials.json", profile_dir / "token.json")
            credentials, refreshed = manager.refresh_silently(); result = {"provider": "google_drive", "profile": args.profile, "authorized": True, "refreshed": refreshed, "refreshable": bool(credentials.refresh_token)}
        else:
            result = registry.verify_rclone(args.profile, args.location); result.update({"provider": "rclone"})
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    if args.provider_command == "update-rclone":
        if not args.force and not settings.auto_update_rclone: raise RuntimeError("Automatic rclone update is disabled. Use --force or enable runtime.auto_update_rclone.")
        result = registry.rclone.self_update(); print(json.dumps({"status": "success", "rclone": result}, ensure_ascii=False, indent=2)); return 0
    if args.provider_command == "setup-google":
        if not _safe_profile(args.profile): raise ValueError("Invalid Google profile name")
        profile_dir = resolve_project_path(settings.provider_profile_dir) / "google" / args.profile; manager = GoogleOAuthManager(profile_dir / "credentials.json", profile_dir / "token.json"); credentials = manager.authorize(open_browser=True)
        save_runtime(provider="google_drive", profile=args.profile, source=f"gdrive://{args.source_folder_id}", target=f"gdrive://{args.target_folder_id}", archive=args.archive_folder_id)
        print(json.dumps({"status": "success", "provider": "google_drive", "profile": args.profile, "authorized": bool(credentials.refresh_token), "active": True}, ensure_ascii=False, indent=2)); return 0
    if args.provider_command == "auth-rclone":
        options = {}
        for item in args.options:
            if "=" not in item: raise ValueError(f"rclone option must use key=value: {item}")
            key, value = item.split("=", 1); options[key] = value
        if args.non_interactive: print(json.dumps(registry.rclone.config_create_non_interactive(args.name, args.backend, options), ensure_ascii=False, indent=2))
        else: registry.rclone.config_interactive(name=args.name, backend=args.backend); print(json.dumps({"status": "success", "provider": "rclone", "remote": args.name}, ensure_ascii=False, indent=2))
        return 0
    if args.provider_command == "setup-rclone":
        registry.rclone.config_interactive(name=args.name, backend=args.backend); save_runtime(provider="rclone", profile=args.name, rclone_remote=args.name, source=f"rclone://{args.source}", target=f"rclone://{args.target}"); print(json.dumps({"status": "success", "provider": "rclone", "remote": args.name, "active": True}, ensure_ascii=False, indent=2)); return 0
    if args.provider_command == "use":
        if args.provider == "local": save_runtime(provider="local", source=args.source, target=args.target)
        elif args.provider == "google_drive":
            if not registry.google_status(args.profile).get("authorized"): raise RuntimeError("Google profile is not authorized; run provider setup-google once")
            save_runtime(provider="google_drive", profile=args.profile, source=args.source, target=args.target, archive=args.archive)
        else:
            if args.profile not in registry.rclone.list_remotes(): raise RuntimeError(f"rclone remote '{args.profile}' does not exist")
            save_runtime(provider="rclone", profile=args.profile, rclone_remote=args.profile, source=args.source, target=args.target)
        print(json.dumps({"status": "success", "active": True}, ensure_ascii=False, indent=2)); return 0
    if args.provider_command == "remove":
        runtime = load_runtime().get("active", {})
        if args.provider == "rclone" and runtime.get("rclone_remote") == args.name: raise RuntimeError("Switch provider before removing the active rclone remote")
        if args.provider == "google_drive" and runtime.get("provider") in {"google_drive", "gdrive"} and runtime.get("profile", "default") == args.name: raise RuntimeError("Switch provider before removing the active Google profile")
        if args.provider == "rclone": registry.rclone.delete_remote(args.name)
        else: registry.remove_google(args.name)
        return 0
    if args.provider_command == "clear": clear_runtime(); print(json.dumps({"status": "success", "message": "Saved provider selection cleared."}, indent=2)); return 0
    return 2


def command_reprocess_subtitles(args) -> int:
    settings = load_settings(args.config)
    if args.scheduled and any(value is not None for value in (args.provider, args.target)): raise ValueError("Scheduled reprocess mode must use the saved active provider configuration")
    provider = (args.provider or settings.provider).lower(); provider = "google_drive" if provider == "gdrive" else provider; settings = replace(settings, provider=provider)
    target = args.target or settings.target; parsed_target = parse_storage_uri(target); expected_scheme = {"local": "local", "google_drive": "gdrive", "rclone": "rclone"}[provider]
    if parsed_target.scheme != expected_scheme: raise ValueError(f"Provider {provider!r} requires {expected_scheme}:// target")
    configure_logging(settings.log_level); readiness = check_unattended(settings, ensure_rclone_binary=(provider == "rclone" and settings.auto_bootstrap_rclone))
    if not readiness.ready: print(json.dumps({"status": "not_ready", "provider": provider, "checks": readiness.checks, "errors": readiness.errors}, ensure_ascii=False, indent=2)); return 3
    selectors = [args.output_folder, args.video_name, args.source]
    if args.reprocess_all and any(selectors): raise ValueError("--all cannot be combined with --output-folder, --video or --source")
    mode = "stt_only" if args.stt_only else "translate_only" if args.translate_only else "full"
    from src.reprocessor import SubtitleReprocessor
    with RunLock(resolve_project_path(settings.run_lock_file)):
        storage = create_storage_provider(provider, settings)
        try:
            reprocessor = SubtitleReprocessor(settings, storage)
            if args.reprocess_all or not any(selectors): result = reprocessor.reprocess_all(parsed_target.value, mode=mode)
            else: result = reprocessor.reprocess(parsed_target.value, mode=mode, output_folder=args.output_folder, video_name=args.video_name, source=args.source)
            if settings.tts_enabled:
                from src.output_postprocessor import OutputPostProcessor
                tts_result = OutputPostProcessor(settings, storage).process_target(parsed_target.value)
                result["tts_postprocessing"] = tts_result
                if tts_result.get("failed"):
                    result["status"] = "error" if settings.tts_required else "partial_failure"
        finally: storage.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") in {"error", "partial_failure"}: return 1
    return 2 if result.get("status") == "partial_translation" else 0


def command_prefetch_whisper(args) -> int:
    settings = load_settings(args.config); configure_logging(settings.log_level)
    from src.stt_engine import STTEngine
    STTEngine(settings); print(json.dumps({"status": "success", "whisper_model": settings.whisper_model, "resource_profile": settings.resource_profile, "whisper_cpu_threads": settings.whisper_cpu_threads}, ensure_ascii=False, indent=2)); return 0


def command_doctor(args) -> int:
    settings = load_settings(args.config); ensure_directories(); checks = {"config": Path(args.config).is_file(), "python": sys.version_info >= (3, 11), "resource_profile": settings.resource_profile, "whisper_model": settings.whisper_model, "whisper_cpu_threads": settings.whisper_cpu_threads, "max_parallel_videos": settings.max_parallel_videos, "detected_logical_cpus": settings.detected_logical_cpus, "detected_memory_gb": settings.detected_memory_gb}
    ffmpeg_check = FFmpegResolver.doctor(settings); checks["ffmpeg"] = ffmpeg_check["available"]; checks["ffmpeg_path"] = ffmpeg_check.get("path", "")
    readiness = check_unattended(settings, ensure_rclone_binary=False); checks["unattended_ready"] = readiness.ready; checks["provider"] = readiness.provider; checks["provider_errors"] = readiness.errors; checks["provider_checks"] = readiness.checks
    checks["tts_enabled"] = settings.tts_enabled; checks["tts_provider"] = settings.tts_provider; checks["tts_model_path"] = settings.tts_model_path; checks["tts_voices_path"] = settings.tts_voices_path
    print(json.dumps(checks, ensure_ascii=False, indent=2)); return 0 if checks["config"] and checks["python"] and checks["ffmpeg"] else 1


def _safe_profile(name: str) -> bool:
    return bool(name) and name not in {".", ".."} and all(ch.isalnum() or ch in "-_." for ch in name)


def main() -> int:
    argv = sys.argv[1:] or ["run", "--scheduled"]; args = build_parser().parse_args(argv)
    try:
        ensure_directories()
        if args.command == "init": ensure_directories(); print(f"Runtime initialized under: {BASE_DIR}"); return 0
        if args.command == "run": return command_run(args)
        if args.command == "duplicates": return command_duplicates(args)
        if args.command == "auth": return command_auth(args)
        if args.command == "provider": return command_provider(args)
        if args.command == "reprocess-subtitles": return command_reprocess_subtitles(args)
        if args.command == "prefetch-whisper": return command_prefetch_whisper(args)
        if args.command == "doctor": return command_doctor(args)
        return 2
    except Exception as exc:
        logging.getLogger(__name__).exception("Command failed")
        print(json.dumps({"status": "error", "error_type": type(exc).__name__, "error": str(exc)}, ensure_ascii=False, indent=2)); return 1


if __name__ == "__main__": sys.exit(main())
