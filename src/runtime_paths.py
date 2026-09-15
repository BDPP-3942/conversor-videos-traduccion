from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "VideoTranslationPipeline"


def user_data_root() -> Path:
    """Return a writable per-user directory for desktop runtime data."""
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return root / APP_NAME


def runtime_storage_paths() -> dict[str, Path]:
    root = user_data_root() / "storage"
    return {
        "root": root,
        "input": root / "input",
        "output": root / "output",
        "work": root / "work",
        "failures": root / "failures",
        "archive": root / "archive",
        "archive_sources": root / "archive" / "sources",
        "logs": root / "logs",
        "state": root / "state",
        "manifests": root / "output" / "_manifests",
    }


def ensure_runtime_storage() -> dict[str, Path]:
    paths = runtime_storage_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths
