from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "VideoTranslationPipeline"
WORKING_DIRECTORY_NAME = "Video Translation Pipeline"


def user_data_root() -> Path:
    """Return the OS-managed writable per-user directory for application state."""
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return root / APP_NAME


def documents_root() -> Path:
    """Return the conventional user Documents folder without requiring elevated access."""
    if os.name == "nt":
        candidate = Path(os.environ.get("USERPROFILE") or Path.home()) / "Documents"
    else:
        candidate = Path.home() / "Documents"
    return candidate


def working_root() -> Path:
    """Return the user-facing default root for source and generated media."""
    return documents_root() / WORKING_DIRECTORY_NAME


def runtime_storage_paths() -> dict[str, Path]:
    """Return separate user-facing media paths and private application state paths."""
    media_root = working_root()
    state_root = user_data_root()
    return {
        "root": state_root,
        "input": media_root / "input",
        "output": media_root / "output",
        "work": state_root / "work",
        "failures": state_root / "failures",
        "archive": state_root / "archive",
        "archive_sources": state_root / "archive" / "sources",
        "logs": state_root / "logs",
        "state": state_root / "state",
        "manifests": state_root / "manifests",
    }


def ensure_runtime_storage() -> dict[str, Path]:
    """Create the writable defaults without touching the installation directory."""
    paths = runtime_storage_paths()
    for key in ("input", "output", "work", "failures", "archive", "archive_sources", "logs", "state", "manifests"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths
