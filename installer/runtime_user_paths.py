"""Configura rutas escribibles para la aplicación PyInstaller empaquetada."""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from pathlib import Path

APP_NAME = "VideoTranslationPipeline"
MEDIA_NAME = "Video Translation Pipeline"


def _user_data_root() -> Path:
    if sys.platform.startswith("win"):
        return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / APP_NAME


def _documents_root() -> Path:
    if sys.platform.startswith("win"):
        return Path(os.environ.get("USERPROFILE") or Path.home()) / "Documents"
    return Path.home() / "Documents"


def install() -> None:
    """Redirige el estado mutable del ejecutable a ubicaciones del usuario."""
    from config import loader as loader_module
    from config import settings as settings_module
    from src.providers import runtime as runtime_module

    user_root = _user_data_root()
    media_root = _documents_root() / MEDIA_NAME
    state_root = user_root / "state"
    storage_root = user_root / "storage"
    secrets_root = user_root / "secrets"
    tools_root = user_root / "tools"

    settings_module.STORAGE_DIR = storage_root
    settings_module.SECRETS_DIR = secrets_root
    runtime_module.RUNTIME_FILE = state_root / "runtime.toml"

    os.environ.setdefault("SOURCE_URI", f"local://{media_root / 'input'}")
    os.environ.setdefault("TARGET_URI", f"local://{media_root / 'output'}")
    os.environ.setdefault("RUN_LOCK_FILE", str(state_root / "run.lock"))
    os.environ.setdefault(
        "LOCAL_TRANSLATION_MODEL_DIR",
        str(tools_root / "models" / "translation" / "madlad400-3b-ct2-int8"),
    )
    os.environ.setdefault("TTS_MODEL_PATH", str(tools_root / "tts" / "kokoro-v1.0.onnx"))
    os.environ.setdefault("TTS_VOICES_PATH", str(tools_root / "tts" / "voices-v1.0.bin"))
    os.environ.setdefault("RCLONE_CONFIG_FILE", str(secrets_root / "rclone" / "rclone.conf"))
    os.environ.setdefault("RCLONE_BINARY_FILE", str(tools_root / "rclone" / "rclone"))
    os.environ.setdefault("PROVIDER_PROFILE_DIR", str(secrets_root / "providers"))

    def load_user_runtime(settings):
        runtime = runtime_module.load_runtime().get("active", {})
        if not isinstance(runtime, dict):
            return settings
        values = {}
        for name in ("provider", "source", "target", "rclone_remote"):
            if name in runtime:
                values[name] = str(runtime[name])
        if "archive" in runtime and runtime.get("provider") in {"google_drive", "gdrive"}:
            values["archive_folder_id"] = str(runtime.get("archive", ""))
        if runtime.get("profile"):
            values["provider_profile_dir"] = secrets_root / "providers" / str(runtime["profile"])
        return replace(settings, **values)

    loader_module._apply_runtime_provider = load_user_runtime

    for path in (
        media_root / "input",
        media_root / "output",
        storage_root / "work",
        storage_root / "failures",
        storage_root / "archive" / "sources",
        storage_root / "logs",
        state_root,
        storage_root / "output" / "_manifests",
        secrets_root,
        tools_root / "models" / "translation",
        tools_root / "tts",
        tools_root / "rclone",
    ):
        path.mkdir(parents=True, exist_ok=True)


install()
