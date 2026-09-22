from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "VideoTranslationPipeline"
WORKING_DIRECTORY_NAME = "Video Translation Pipeline"


def user_data_root() -> Path:
    """Devuelve la carpeta del sistema para el estado privado de la aplicación."""
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return root / APP_NAME


def documents_root() -> Path:
    """Devuelve la carpeta Documentos convencional sin requerir permisos elevados."""
    if os.name == "nt":
        return Path(os.environ.get("USERPROFILE") or Path.home()) / "Documents"
    return Path.home() / "Documents"


def working_root() -> Path:
    """Devuelve la raíz visible para los vídeos de entrada y resultados."""
    return documents_root() / WORKING_DIRECTORY_NAME


def runtime_storage_paths() -> dict[str, Path]:
    """Devuelve por separado las rutas multimedia y el estado privado de la aplicación."""
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
    """Crea las rutas predeterminadas sin escribir en la carpeta de instalación."""
    paths = runtime_storage_paths()
    # Solo se crean al arrancar las carpetas visibles de trabajo. El resto del
    # estado privado se crea de forma perezosa cuando una etapa lo necesita.
    for key in ("input", "output"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths
