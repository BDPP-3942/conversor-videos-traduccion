from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath
from zipfile import ZipFile

MEDIA_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v"}
MOJIBAKE_MARKERS = ("Ã", "Â", "â", "ð", "�", "╠", "╣", "┬")


@dataclass(slots=True)
class ZipExtractionResult:
    archive: Path
    root: Path
    files: list[Path] = field(default_factory=list)
    directories: list[Path] = field(default_factory=list)


class ZipSecurityError(ValueError):
    """Indica una entrada ZIP que no puede extraerse de forma segura."""


class ZipExtractor:
    """Extrae ZIP de forma segura y normaliza nombres de raíz multiplataforma."""

    @staticmethod
    def _is_windows_reserved_component(name: str) -> bool:
        stem = name.split(".", 1)[0].rstrip(" .").upper()
        return stem in {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }

    @staticmethod
    def _safe_directory_name(name: str) -> str:
        """Crea un nombre de raíz de extracción portable a partir del nombre del ZIP."""
        normalized = unicodedata.normalize("NFC", name)
        invalid = '<>:"/\\|?*'
        sanitized = "".join("_" if char in invalid or unicodedata.category(char) == "Cc" else char for char in normalized)
        sanitized = sanitized.rstrip(" .")
        if ZipExtractor._is_windows_reserved_component(sanitized):
            sanitized = f"_{sanitized}"
        return sanitized or "archive"

    @staticmethod
    def _normalize_member_name(name: str) -> str:
        name = unicodedata.normalize("NFC", name.replace("\\", "/"))
        parts = []
        for component in PurePosixPath(name).parts:
            if component in ("", "."):
                continue
            if component == "..":
                raise ZipSecurityError(f"Ruta ZIP insegura: {name!r}")
            parts.append(component)
        return "/".join(parts)

    @staticmethod
    def _validate_member(name: str) -> str:
        normalized = ZipExtractor._normalize_member_name(name)
        if not normalized:
            raise ZipSecurityError("Entrada ZIP sin nombre")
        if PureWindowsPath(normalized).is_absolute() or PurePosixPath(normalized).is_absolute():
            raise ZipSecurityError(f"Ruta ZIP absoluta no permitida: {name!r}")
        if len(normalized) > 32767:
            raise ZipSecurityError(f"Ruta ZIP demasiado larga: {name!r}")
        return normalized

    def extract(self, archive: Path, destination: Path) -> ZipExtractionResult:
        archive = Path(archive)
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)
        root = destination / self._safe_directory_name(archive.stem)
        root.mkdir(parents=True, exist_ok=True)
        result = ZipExtractionResult(archive=archive, root=root)
        with ZipFile(archive) as zf:
            for info in zf.infolist():
                member = self._validate_member(info.filename)
                target = root / member
                resolved = target.resolve()
                if root.resolve() not in resolved.parents and resolved != root.resolve():
                    raise ZipSecurityError(f"Extracción fuera del directorio permitido: {info.filename!r}")
                if info.is_dir() or info.filename.endswith(("/", "\\")):
                    target.mkdir(parents=True, exist_ok=True)
                    result.directories.append(target)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as source, target.open("wb") as sink:
                    sink.write(source.read())
                result.files.append(target)
        return result
