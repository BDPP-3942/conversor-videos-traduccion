from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config.settings import AppSettings, resolve_project_path
from src.auth.google_oauth import GoogleOAuthManager
from src.auth.rclone_manager import RcloneManager
from src.storage.uri import parse_storage_uri


@dataclass(frozen=True)
class Readiness:
    ready: bool
    provider: str
    checks: dict[str, object]
    errors: list[str]


def _check_tts(settings: AppSettings, checks: dict[str, object], errors: list[str]) -> None:
    if not settings.tts_enabled:
        checks["tts_enabled"] = False
        return

    checks["tts_enabled"] = True
    model_path = resolve_project_path(settings.tts_model_path)
    voices_path = resolve_project_path(settings.tts_voices_path)
    checks["tts_model"] = str(model_path)
    checks["tts_model_exists"] = model_path.is_file()
    checks["tts_voices"] = str(voices_path)
    checks["tts_voices_exists"] = voices_path.is_file()
    try:
        import kokoro_onnx  # noqa: F401

        checks["tts_dependency"] = True
    except ImportError:
        checks["tts_dependency"] = False
        errors.append("TTS is enabled but the optional 'kokoro-onnx' dependency is not installed.")

    if not model_path.is_file():
        errors.append(f"TTS model file is missing: {model_path}")
    if not voices_path.is_file():
        errors.append(f"TTS voices file is missing: {voices_path}")


def check_unattended(settings: AppSettings, *, ensure_rclone_binary: bool = True) -> Readiness:
    provider = settings.provider.lower()
    checks: dict[str, object] = {}
    errors: list[str] = []
    _check_tts(settings, checks, errors)

    source = parse_storage_uri(settings.source)
    target = parse_storage_uri(settings.target)
    if source.scheme not in {"local", "gdrive", "rclone", "http", "https"}:
        errors.append(f"Unsupported source scheme: {source.scheme}")
    if target.scheme not in {"local", "gdrive", "rclone"}:
        errors.append(f"Unsupported target scheme: {target.scheme}")

    if source.scheme in {"http", "https"}:
        checks["remote_source"] = "HTTP(S)"
    elif source.scheme == "local":
        checks["local_input"] = Path(source.value).exists()
    else:
        checks["remote_source"] = source.scheme

    if target.scheme == "local":
        checks["local_output_parent"] = Path(target.value).parent.exists()

    if target.scheme == "gdrive":
        manager = GoogleOAuthManager(settings.google_credentials_file, settings.google_token_file)
        try:
            credentials, refreshed = manager.refresh_silently()
            checks["google_authorized"] = True
            checks["google_refreshable"] = bool(credentials.refresh_token)
            checks["google_token_refreshed"] = refreshed
        except Exception as exc:
            checks["google_authorized"] = False
            errors.append(str(exc))
    elif target.scheme == "rclone":
        manager = RcloneManager(settings.rclone_binary_file, settings.rclone_config_file)
        try:
            binary = manager.ensure_binary() if ensure_rclone_binary else settings.rclone_binary_file
            checks["rclone_binary_exists"] = binary.is_file()
            remotes = manager.list_remotes() if binary.is_file() else []
            if settings.rclone_remote not in remotes:
                errors.append(f"Configured rclone remote '{settings.rclone_remote}' does not exist.")
            if not settings.rclone_config_file.is_file():
                errors.append("rclone configuration file is missing.")
        except Exception as exc:
            errors.append(f"rclone readiness check failed: {exc}")

    if provider not in {"local", "google_drive", "gdrive", "rclone"}:
        errors.append(f"Unsupported active provider: {provider}")

    return Readiness(not errors, provider, checks, errors)
