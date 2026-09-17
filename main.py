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
from src.resource_profile import safe_parallelism
from src.runtime_lock import RunLock
from src.storage.factory import create_storage_provider
from src.storage.uri import parse_storage_uri

logger = logging.getLogger(__name__)


def configure_logging(log_level: str) -> None:
    """Configura el registro en consola y en el archivo persistente del pipeline."""
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
    """Construye el parser público de la CLI y sus subcomandos."""
    parser = argparse.ArgumentParser(description="Pipeline desatendido de STT y traducción de vídeo/audio")
    parser.add_argument(
        "--config",
        type=Path,
        default=BASE_DIR / "config" / "app.toml",
        help="Ruta al archivo TOML de configuración",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser(
        "run",
        help="Ejecuta un lote de procesamiento desatendido",
        description="Procesa vídeo/audio mediante STT, traducción y TTS opcional.",
    )
    run.add_argument("--scheduled", action="store_true", help="Ejecuta sin navegador ni entrada interactiva")
    run.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida el runtime y muestra los ajustes efectivos sin procesar archivos",
    )
    run.add_argument(
        "--provider",
        choices=["local", "google_drive", "gdrive", "rclone"],
        default=None,
        help="Sobrescribe el proveedor de almacenamiento configurado",
    )
    run.add_argument("--source", default=None, help="Sobrescribe la URI source de almacenamiento")
    run.add_argument("--target", default=None, help="Sobrescribe la URI target de almacenamiento")
    run.add_argument(
        "--no-retain-sources",
        action="store_true",
        help="No conserva los archivos fuente tras el procesamiento local",
    )
    run.add_argument(
        "--no-resume",
        action="store_true",
        help="Desactiva la reutilización de resultados compatibles",
    )
    run.add_argument(
        "--no-name-migration",
        action="store_true",
        help="Desactiva la normalización de nombres heredados",
    )
    run.add_argument(
        "--parallel-videos",
        type=int,
        default=None,
        help="Máximo de workers de vídeo; 0 selecciona AUTO",
    )
    run.add_argument(
        "--translation-batch-size",
        type=int,
        default=None,
        help="Sobrescribe el tamaño de lote de traducción",
    )
    run.add_argument(
        "--whisper-beam-size",
        type=int,
        default=None,
        help="Sobrescribe el beam size de Whisper",
    )
    run.add_argument(
        "--whisper-cpu-threads",
        type=int,
        default=None,
        help="Sobrescribe los hilos de CPU de Whisper; 0 mantiene AUTO",
    )
    run.add_argument(
        "--no-ffmpeg-copy",
        action="store_true",
        help="Desactiva la optimización stream-copy de FFmpeg",
    )
    webm_group = run.add_mutually_exclusive_group()
    webm_group.add_argument(
        "--generate-webm",
        dest="generate_webm",
        action="store_true",
        help="Fuerza la generación de la salida WebM secundaria",
    )
    webm_group.add_argument(
        "--no-webm",
        dest="generate_webm",
        action="store_false",
        help="Impide la generación de la salida WebM secundaria",
    )
    run.set_defaults(generate_webm=None)

    duplicates = sub.add_parser(
        "duplicates",
        help="Inspecciona y gestiona carpetas de salida duplicadas",
        description="Analiza y elimina opcionalmente duplicados mediante el plan persistido.",
    )
    duplicates.add_argument(
        "--target",
        type=Path,
        default=BASE_DIR / "storage" / "output",
        help="Directorio local de salida; predeterminado: storage/output",
    )
    duplicate_sub = duplicates.add_subparsers(dest="duplicates_command", required=True)
    duplicate_sub.add_parser("scan", help="Detecta duplicados sin modificar resultados")
    duplicate_sub.add_parser("analyze", help="Analiza duplicados y persiste el plan de eliminación")
    delete_duplicates = duplicate_sub.add_parser("delete", help="Elimina únicamente los duplicados del plan persistido")
    delete_duplicates.add_argument("--dry-run", action="store_true", help="Muestra qué se eliminaría sin borrar nada")

    auth = sub.add_parser(
        "auth",
        help="Autenticación interactiva de un solo uso",
        description="Autoriza un proveedor para un perfil persistente.",
    )
    auth.add_argument("provider", choices=["google"], help="Proveedor de autenticación")
    auth.add_argument("--profile", default="default", help="Nombre del perfil; predeterminado: default")

    provider = sub.add_parser(
        "provider",
        help="Configura y selecciona perfiles persistentes",
        description="Gestiona perfiles de proveedores y la selección activa del runtime.",
    )
    provider_sub = provider.add_subparsers(dest="provider_command", required=True)
    provider_sub.add_parser("bootstrap", help="Instala el binario gestionado de rclone")
    provider_sub.add_parser("list", help="Lista los perfiles configurados y el runtime activo")
    verify = provider_sub.add_parser(
        "verify",
        help="Comprueba credenciales cloud en modo de solo lectura",
        description="Comprueba el acceso sin cambiar la configuración.",
    )
    verify.add_argument("provider", choices=["google_drive", "rclone"], help="Proveedor cloud")
    verify.add_argument("--profile", default="default", help="Perfil; predeterminado: default")
    verify.add_argument("--location", default="", help="Carpeta de rclone para la comprobación")
    update = provider_sub.add_parser("update-rclone", help="Actualiza explícitamente el binario gestionado de rclone")
    update.add_argument(
        "--force",
        action="store_true",
        help="Actualiza aunque las actualizaciones automáticas estén desactivadas",
    )
    setup_google = provider_sub.add_parser(
        "setup-google", help="Configura Google Drive: OAuth, carpetas y perfil activo"
    )
    setup_google.add_argument("--profile", default="default", help="Perfil de Google; predeterminado: default")
    setup_google.add_argument("--source-folder-id", required=True, help="ID de la carpeta de origen de Google Drive")
    setup_google.add_argument("--target-folder-id", required=True, help="ID de la carpeta de destino de Google Drive")
    setup_google.add_argument("--archive-folder-id", default="", help="ID opcional de la carpeta de archivo")
    auth_rclone = provider_sub.add_parser("auth-rclone", help="Configura un remote de rclone")
    auth_rclone.add_argument("name", help="Nombre del remote de rclone")
    auth_rclone.add_argument("backend", help="Tipo de backend de rclone")
    auth_rclone.add_argument("options", nargs="*", help="Ajustes opcionales como key=value")
    auth_rclone.add_argument(
        "--non-interactive", action="store_true", help="Crea el remote sin configuración interactiva"
    )
    setup_rclone = provider_sub.add_parser("setup-rclone", help="Configura rclone y source/target activos")
    setup_rclone.add_argument("name", help="Nombre del remote de rclone")
    setup_rclone.add_argument("backend", help="Tipo de backend de rclone")
    setup_rclone.add_argument("--source", required=True, help="Ruta remota de entrada, por ejemplo input")
    setup_rclone.add_argument("--target", required=True, help="Ruta remota de salida, por ejemplo output")
    setup_rclone.add_argument("--option", action="append", default=[], help="Opción de rclone como key=value")
    use = provider_sub.add_parser("use", help="Selecciona el proveedor/perfil activo")
    use.add_argument("provider", choices=["local", "google_drive", "rclone"], help="Proveedor que se activará")
    use.add_argument("--profile", default="default", help="Perfil del proveedor")
    use.add_argument("--source", required=True, help="URI source activa")
    use.add_argument("--target", required=True, help="URI target activa")
    use.add_argument("--archive", default="", help="Ubicación opcional de archivo")
    remove = provider_sub.add_parser("remove", help="Elimina un perfil cloud que ya no se utilice")
    remove.add_argument("provider", choices=["google_drive", "rclone"], help="Proveedor cloud")
    remove.add_argument("name", help="Nombre del perfil o remote")
    provider_sub.add_parser("clear", help="Borra la selección de proveedor guardada")

    reprocess = sub.add_parser(
        "reprocess-subtitles",
        help="Reprocesa STT y/o traducción sin regenerar medios",
        description="Regenera las etapas de subtítulos de resultados existentes.",
    )
    mode = reprocess.add_mutually_exclusive_group()
    mode.add_argument("--stt-only", action="store_true", help="Regenera únicamente la transcripción original")
    mode.add_argument("--translate-only", action="store_true", help="Regenera únicamente el VTT traducido")
    reprocess.add_argument("--output-folder", default=None, help="Carpeta de salida existente que se procesará")
    reprocess.add_argument(
        "--all",
        dest="reprocess_all",
        action="store_true",
        help="Procesa todas las carpetas elegibles",
    )
    reprocess.add_argument("--video", dest="video_name", default=None, help="Nombre del vídeo/fuente a seleccionar")
    reprocess.add_argument("--source", default=None, help="URI de origen o selector de fuente")
    reprocess.add_argument("--scheduled", action="store_true", help="Usa la configuración guardada del proveedor")
    reprocess.add_argument(
        "--provider",
        choices=["local", "google_drive", "gdrive", "rclone"],
        default=None,
        help="Sobrescribe el proveedor de almacenamiento",
    )
    reprocess.add_argument("--target", default=None, help="Sobrescribe la URI target de almacenamiento")
    sub.add_parser(
        "prefetch-whisper",
        help="Descarga/inicializa el modelo de Whisper seleccionado",
        description="Inicializa el modelo configurado de Whisper/STT.",
    )
    sub.add_parser(
        "doctor",
        help="Comprueba la preparación del runtime interactivo y desatendido",
        description="Comprueba configuración, Python, FFmpeg, Whisper y proveedores.",
    )
    sub.add_parser(
        "init",
        help="Crea los directorios de runtime",
        description="Crea los directorios requeridos por el pipeline.",
    )
    return parser


def _build_locations(settings, provider: str, source: str | None, target: str | None):
    """Resuelve las ubicaciones efectivas respetando los valores explícitos de la CLI."""
    if source and target:
        return source, target
    return settings.source, settings.target


def _run_automatic_deduplication(settings, target: str) -> dict[str, Any] | None:
    """Ejecuta la deduplicación automática cuando está habilitada para almacenamiento local."""
    if not getattr(settings, "automatic_output_deduplication", True) or settings.provider.lower() != "local":
        return None
    from src.output_deduplicator import OutputDeduplicator

    target_path = resolve_project_path(target.removeprefix("local://"))
    deduplicator = OutputDeduplicator(target_path)
    deduplicator.scan_and_persist()
    plan = deduplicator.analyze_and_persist()
    results = deduplicator.delete()
    return {"plan": plan, "results": results}


def _apply_run_overrides(settings, args):
    """Aplica a la configuración las opciones de ejecución recibidas desde la CLI."""
    if args.parallel_videos is not None:
        requested = 0 if args.parallel_videos == 0 else max(1, args.parallel_videos)
        settings = replace(settings, max_parallel_videos=requested)
        settings = replace(settings, max_parallel_videos=safe_parallelism(settings))
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
    return settings


def command_run(args) -> int:
    """Ejecuta el pipeline principal con el proveedor y las opciones seleccionadas."""
    settings = load_settings(args.config)
    provider = (args.provider or settings.provider).lower()
    if args.scheduled and any(value is not None for value in (args.provider, args.source, args.target)):
        raise ValueError("El modo programado debe utilizar la configuración guardada del proveedor activo")
    settings = replace(settings, provider=provider)
    source, target = _build_locations(settings, provider, args.source, args.target)
    parsed_source = parse_storage_uri(source)
    parsed_target = parse_storage_uri(target)
    expected_scheme = {"local": "local", "google_drive": "gdrive", "gdrive": "gdrive", "rclone": "rclone"}[provider]
    if parsed_source.scheme != expected_scheme or parsed_target.scheme != expected_scheme:
        raise ValueError(f"El proveedor {provider!r} requiere source y target con esquema {expected_scheme}://")
    if provider == "local" and args.no_retain_sources:
        settings = replace(settings, local_retain_sources=False)
    if args.no_resume:
        settings = replace(settings, resume_enabled=False)
    if args.no_name_migration:
        settings = replace(settings, normalize_legacy_names=False)
    settings = _apply_run_overrides(settings, args)
    configure_logging(settings.log_level)
    if provider == "rclone" and settings.auto_update_rclone:
        try:
            RcloneManager(
                resolve_project_path(settings.rclone_binary_file), resolve_project_path(settings.rclone_config_file)
            ).self_update()
        except Exception as exc:
            logger.warning("Se omite la actualización automática de rclone: %s", exc)
    readiness = check_unattended(
        settings, ensure_rclone_binary=(provider == "rclone" and settings.auto_bootstrap_rclone)
    )
    if not readiness.ready:
        print(
            json.dumps(
                {"status": "not_ready", "provider": provider, "checks": readiness.checks, "errors": readiness.errors},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "ready",
                    "provider": provider,
                    "checks": readiness.checks,
                    "effective_parallelism": safe_parallelism(settings),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    from src.pipeline import MediaPipeline

    with RunLock(resolve_project_path(settings.run_lock_file)):
        storage = create_storage_provider(provider, settings)
        try:
            result = MediaPipeline(settings, storage).run(parsed_source.value, parsed_target.value)
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
    """Gestiona el análisis y la eliminación controlada de duplicados."""
    settings = load_settings(args.config)
    configure_logging(settings.log_level)
    from src.output_deduplicator import OutputDeduplicator

    deduplicator = OutputDeduplicator(args.target)
    if args.duplicates_command == "scan":
        payload = deduplicator.scan_and_persist()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if args.duplicates_command == "analyze":
        payload = deduplicator.analyze_and_persist()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    results = deduplicator.delete(dry_run=args.dry_run)
    print(json.dumps({"status": "success", "dry_run": args.dry_run, "results": results}, ensure_ascii=False, indent=2))
    return 0


def command_auth(args) -> int:
    """Ejecuta la autorización interactiva de un perfil de Google."""
    settings = load_settings(args.config)
    profile_dir = resolve_project_path(settings.provider_profile_dir) / "google" / args.profile
    manager = GoogleOAuthManager(profile_dir / "credentials.json", profile_dir / "token.json")
    credentials = manager.authorize(open_browser=True)
    print(
        json.dumps(
            {
                "provider": "google_drive",
                "profile": args.profile,
                "authorized": bool(credentials.valid or credentials.refresh_token),
                "token_file": str(manager.token_file),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_provider(args) -> int:
    """Ejecuta las operaciones de gestión de proveedores."""
    settings = load_settings(args.config)
    registry = ProviderRegistry(settings)
    if args.provider_command == "bootstrap":
        path = registry.rclone.ensure_binary()
        print(json.dumps({"status": "success", "rclone": str(path), "version": registry.rclone.version()}, indent=2))
        return 0
    if args.provider_command == "list":
        result = registry.list_profiles()
        result["runtime"] = load_runtime().get("active", {})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.provider_command == "verify":
        if args.provider == "google_drive":
            profile_dir = resolve_project_path(settings.provider_profile_dir) / "google" / args.profile
            manager = GoogleOAuthManager(profile_dir / "credentials.json", profile_dir / "token.json")
            credentials, refreshed = manager.refresh_silently()
            result = {
                "provider": "google_drive",
                "profile": args.profile,
                "authorized": True,
                "refreshed": refreshed,
                "refreshable": bool(credentials.refresh_token),
            }
        else:
            result = registry.verify_rclone(args.profile, args.location)
            result.update({"provider": "rclone"})
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.provider_command == "update-rclone":
        if not args.force and not settings.auto_update_rclone:
            raise RuntimeError(
                "La actualización automática de rclone está desactivada. "
                "Usa --force o activa runtime.auto_update_rclone."
            )
        result = registry.rclone.self_update()
        print(json.dumps({"status": "success", "rclone": result}, ensure_ascii=False, indent=2))
        return 0
    if args.provider_command == "setup-google":
        if not _safe_profile(args.profile):
            raise ValueError("El nombre del perfil de Google no es válido")
        profile_dir = resolve_project_path(settings.provider_profile_dir) / "google" / args.profile
        manager = GoogleOAuthManager(profile_dir / "credentials.json", profile_dir / "token.json")
        credentials = manager.authorize(open_browser=True)
        save_runtime(
            provider="google_drive",
            profile=args.profile,
            source=f"gdrive://{args.source_folder_id}",
            target=f"gdrive://{args.target_folder_id}",
            archive=args.archive_folder_id,
        )
        print(
            json.dumps(
                {
                    "status": "success",
                    "provider": "google_drive",
                    "profile": args.profile,
                    "authorized": bool(credentials.refresh_token),
                    "active": True,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.provider_command == "auth-rclone":
        options = {}
        for item in args.options:
            if "=" not in item:
                raise ValueError(f"La opción de rclone debe utilizar key=value: {item}")
            key, value = item.split("=", 1)
            options[key] = value
        if args.non_interactive:
            print(
                json.dumps(
                    registry.rclone.config_create_non_interactive(args.name, args.backend, options),
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            registry.rclone.config_interactive(name=args.name, backend=args.backend)
            print(
                json.dumps(
                    {"status": "success", "provider": "rclone", "remote": args.name}, ensure_ascii=False, indent=2
                )
            )
        return 0
    if args.provider_command == "setup-rclone":
        registry.rclone.config_interactive(name=args.name, backend=args.backend)
        save_runtime(
            provider="rclone",
            profile=args.name,
            rclone_remote=args.name,
            source=f"rclone://{args.source}",
            target=f"rclone://{args.target}",
        )
        print(
            json.dumps(
                {"status": "success", "provider": "rclone", "remote": args.name, "active": True},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.provider_command == "use":
        if args.provider == "local":
            save_runtime(provider="local", source=args.source, target=args.target)
        elif args.provider == "google_drive":
            if not registry.google_status(args.profile).get("authorized"):
                raise RuntimeError("El perfil de Google no está autorizado; ejecuta una vez provider setup-google")
            save_runtime(
                provider="google_drive",
                profile=args.profile,
                source=args.source,
                target=args.target,
                archive=args.archive,
            )
        else:
            if args.profile not in registry.rclone.list_remotes():
                raise RuntimeError(f"El remote de rclone '{args.profile}' no existe")
            save_runtime(
                provider="rclone",
                profile=args.profile,
                rclone_remote=args.profile,
                source=args.source,
                target=args.target,
            )
        print(json.dumps({"status": "success", "active": True}, ensure_ascii=False, indent=2))
        return 0
    if args.provider_command == "remove":
        runtime = load_runtime().get("active", {})
        if args.provider == "rclone" and runtime.get("rclone_remote") == args.name:
            raise RuntimeError("Cambia de proveedor antes de eliminar el remote de rclone activo")
        if (
            args.provider == "google_drive"
            and runtime.get("provider") in {"google_drive", "gdrive"}
            and runtime.get("profile", "default") == args.name
        ):
            raise RuntimeError("Cambia de proveedor antes de eliminar el perfil de Google activo")
        if args.provider == "rclone":
            registry.rclone.delete_remote(args.name)
        else:
            registry.remove_google(args.name)
        return 0
    if args.provider_command == "clear":
        clear_runtime()
        print(
            json.dumps(
                {"status": "success", "message": "Se ha borrado la selección de proveedor guardada."},
                indent=2,
            )
        )
        return 0
    return 2


def command_reprocess_subtitles(args) -> int:
    """Regenera las etapas de subtítulos de resultados existentes."""
    settings = load_settings(args.config)
    if args.scheduled and any(value is not None for value in (args.provider, args.target)):
        raise ValueError(
            "El modo de reprocesamiento programado debe utilizar la configuración guardada del proveedor activo"
        )
    provider = (args.provider or settings.provider).lower()
    provider = "google_drive" if provider == "gdrive" else provider
    settings = replace(settings, provider=provider)
    target = args.target or settings.target
    parsed_target = parse_storage_uri(target)
    expected_scheme = {"local": "local", "google_drive": "gdrive", "rclone": "rclone"}[provider]
    if parsed_target.scheme != expected_scheme:
        raise ValueError(f"El proveedor {provider!r} requiere un target con esquema {expected_scheme}://")
    configure_logging(settings.log_level)
    readiness = check_unattended(
        settings, ensure_rclone_binary=(provider == "rclone" and settings.auto_bootstrap_rclone)
    )
    if not readiness.ready:
        print(
            json.dumps(
                {"status": "not_ready", "provider": provider, "checks": readiness.checks, "errors": readiness.errors},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3
    selectors = [args.output_folder, args.video_name, args.source]
    if args.reprocess_all and any(selectors):
        raise ValueError("--all no se puede combinar con --output-folder, --video o --source")
    mode = "stt_only" if args.stt_only else "translate_only" if args.translate_only else "full"
    from src.reprocessor import SubtitleReprocessor

    with RunLock(resolve_project_path(settings.run_lock_file)):
        storage = create_storage_provider(provider, settings)
        try:
            reprocessor = SubtitleReprocessor(settings, storage)
            if args.reprocess_all or not any(selectors):
                result = reprocessor.reprocess_all(parsed_target.value, mode=mode)
            else:
                result = reprocessor.reprocess(
                    parsed_target.value,
                    mode=mode,
                    output_folder=args.output_folder,
                    video_name=args.video_name,
                    source=args.source,
                )
        finally:
            storage.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") in {"error", "partial_failure"}:
        return 1
    return 2 if result.get("status") == "partial_translation" else 0


def command_prefetch_whisper(args) -> int:
    """Inicializa el modelo de Whisper configurado."""
    settings = load_settings(args.config)
    configure_logging(settings.log_level)
    from src.stt_engine import STTEngine

    STTEngine(settings)
    print(
        json.dumps(
            {
                "status": "success",
                "whisper_model": settings.whisper_model,
                "resource_profile": settings.resource_profile,
                "whisper_cpu_threads": settings.whisper_cpu_threads,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_doctor(args) -> int:
    """Comprueba la preparación del entorno y de los proveedores."""
    settings = load_settings(args.config)
    ensure_directories()
    checks = {"config": Path(args.config).is_file(), "python": sys.version_info >= (3, 11)}
    checks["resource_profile"] = settings.resource_profile
    checks["whisper_model"] = settings.whisper_model
    checks["whisper_cpu_threads"] = settings.whisper_cpu_threads
    checks["max_parallel_videos"] = settings.max_parallel_videos
    checks["detected_logical_cpus"] = settings.detected_logical_cpus
    checks["detected_memory_gb"] = settings.detected_memory_gb
    ffmpeg_check = FFmpegResolver.doctor(settings)
    checks["ffmpeg"] = ffmpeg_check["available"]
    checks["ffmpeg_path"] = ffmpeg_check.get("path", "")
    readiness = check_unattended(settings, ensure_rclone_binary=False)
    checks["unattended_ready"] = readiness.ready
    checks["provider"] = readiness.provider
    checks["provider_errors"] = readiness.errors
    checks["provider_checks"] = readiness.checks
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0 if checks["config"] and checks["python"] and checks["ffmpeg"] else 1


def _safe_profile(name: str) -> bool:
    """Comprueba que un nombre de perfil no pueda escapar de su directorio."""
    return bool(name) and name not in {".", ".."} and all(ch.isalnum() or ch in "-_." for ch in name)


def main() -> int:
    """Despacha la orden solicitada y devuelve su código de salida."""
    argv = sys.argv[1:] or ["run", "--scheduled"]
    args = build_parser().parse_args(argv)
    try:
        ensure_directories()
        if args.command == "init":
            ensure_directories()
            print(f"Runtime inicializado en: {BASE_DIR}")
            return 0
        if args.command == "run":
            return command_run(args)
        if args.command == "duplicates":
            return command_duplicates(args)
        if args.command == "auth":
            return command_auth(args)
        if args.command == "provider":
            return command_provider(args)
        if args.command == "reprocess-subtitles":
            return command_reprocess_subtitles(args)
        if args.command == "prefetch-whisper":
            return command_prefetch_whisper(args)
        if args.command == "doctor":
            return command_doctor(args)
        return 2
    except Exception as exc:
        logging.getLogger(__name__).exception("Ha fallado el comando")
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
