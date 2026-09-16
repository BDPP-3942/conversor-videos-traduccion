from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath
from zipfile import ZipFile

MEDIA_EXTENSIONS = {".mp4", ".mp3", ".wmv", ".mov", ".mkv", ".avi"}
# Caracteres que suelen aparecer cuando bytes UTF-8 se interpretan como CP437.
# Solo actúan como señal; la reparación debe poder revertirse sin pérdida.
MOJIBAKE_MARKERS = frozenset("ÃÂÐÑâ├┤┬╠╣╬▒░")


@dataclass
class ExtractionResult:
    media: list[Path] = field(default_factory=list)
    nested_zips: list[Path] = field(default_factory=list)
    ignored_files: list[Path] = field(default_factory=list)
    max_depth_reached: int = 0
    extracted_files: int = 0
    extracted_bytes: int = 0


class ZipExtractor:
    """Extrae ZIPs anidados manteniendo el árbol y aplicando límites de seguridad."""

    def __init__(self, max_depth: int, max_files: int, max_total_size: int) -> None:
        if max_depth < 0 or max_files <= 0 or max_total_size <= 0:
            raise ValueError("Los límites de extracción ZIP deben ser positivos")
        self.max_depth = max_depth
        self.max_files = max_files
        self.max_total_size = max_total_size

    def extract_zip(self, zip_path: Path, extract_to: Path) -> ExtractionResult:
        if not zip_path.is_file():
            raise FileNotFoundError(f"No se encontró el ZIP: {zip_path}")
        extract_to.mkdir(parents=True, exist_ok=True)
        result = ExtractionResult()
        self._extract_recursive(zip_path.resolve(), extract_to, 0, result, set())
        return result

    def _extract_recursive(
        self,
        zip_path: Path,
        extract_to: Path,
        depth: int,
        result: ExtractionResult,
        processed: set[Path],
    ) -> None:
        if depth > self.max_depth:
            raise ValueError(f"Se ha superado la profundidad máxima de anidación ZIP: {self.max_depth}")
        if zip_path in processed:
            return
        processed.add(zip_path)
        result.max_depth_reached = max(result.max_depth_reached, depth)

        current_dir = extract_to / self._safe_directory_name(zip_path.stem)
        if current_dir.exists():
            raise ValueError(f"Colisión en el directorio de extracción ZIP: {current_dir.name}")
        current_dir.mkdir(parents=True, exist_ok=False)

        with ZipFile(zip_path, "r") as archive:
            members = [m for m in archive.infolist() if not self._is_ignored_name(m.filename)]
            self._validate_archive(members, current_dir, result)
            self._extract_members(archive, members, current_dir)

        for member in members:
            if member.is_dir():
                continue
            extracted_path = (current_dir / self._normalized_member_name(member)).resolve()
            suffix = extracted_path.suffix.lower()
            if suffix in MEDIA_EXTENSIONS:
                result.media.append(extracted_path)
            elif suffix == ".zip":
                result.nested_zips.append(extracted_path)
                self._extract_recursive(extracted_path, extracted_path.parent, depth + 1, result, processed)
            else:
                result.ignored_files.append(extracted_path)

    def _validate_archive(self, members, destination: Path, result: ExtractionResult) -> None:
        destination = destination.resolve()
        seen_targets: set[str] = set()
        for member in members:
            name = self._normalized_member_name(member)
            self._validate_member_name(name)
            target = (destination / name).resolve()
            if not target.is_relative_to(destination):
                raise ValueError(f"Se ha detectado una ruta ZIP no segura: {member.filename}")
            if self._is_symlink(member):
                raise ValueError(f"No se permiten entradas symlink en los ZIP: {member.filename}")
            collision_key = unicodedata.normalize("NFC", target.as_posix()).casefold()
            if collision_key in seen_targets:
                raise ValueError(f"Se ha detectado una colisión de ruta ZIP: {member.filename}")
            seen_targets.add(collision_key)
            if member.is_dir():
                continue
            result.extracted_files += 1
            result.extracted_bytes += member.file_size
            if result.extracted_files > self.max_files:
                raise ValueError(f"Se ha superado el número máximo de archivos extraídos: {self.max_files}")
            if result.extracted_bytes > self.max_total_size:
                raise ValueError(f"Se ha superado el tamaño máximo de extracción ZIP: {self.max_total_size} bytes")

    @classmethod
    def _validate_member_name(cls, name: str) -> None:
        if not name or "\x00" in name:
            raise ValueError(f"Se ha detectado una ruta ZIP no segura: {name!r}")
        if PurePosixPath(name).is_absolute() or PureWindowsPath(name).is_absolute():
            raise ValueError(f"Se ha detectado una ruta ZIP no segura: {name}")
        if PureWindowsPath(name).drive or PureWindowsPath(name).root:
            raise ValueError(f"Se ha detectado una ruta ZIP no segura: {name}")
        components = [part for part in name.split("/") if part not in {"", "."}]
        if any(part == ".." for part in components):
            raise ValueError(f"Se ha detectado una ruta ZIP no segura: {name}")
        for part in components:
            if cls._is_windows_reserved_component(part):
                raise ValueError(f"No se permite el componente de ruta ZIP reservado de Windows: {name}")

    @staticmethod
    def _extract_members(archive: ZipFile, members, destination: Path) -> None:
        destination = destination.resolve()
        for member in members:
            name = ZipExtractor._normalized_member_name(member)
            target = (destination / name).resolve()
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as source, target.open("xb") as output:
                while chunk := source.read(1024 * 1024):
                    output.write(chunk)

    @staticmethod
    def _is_symlink(member) -> bool:
        return ((member.external_attr >> 16) & 0o170000) == 0o120000

    @staticmethod
    def _is_ignored_name(name: str) -> bool:
        normalized = name.replace("\\", "/")
        return normalized.startswith("__MACOSX/") or "/__MACOSX/" in normalized or normalized.endswith(".DS_Store")

    @staticmethod
    def _normalized_member_name(member) -> str:
        """Devuelve una ruta Unicode canónica antes de acceder al sistema de archivos.

        Los nombres ZIP sin indicador UTF-8 se decodifican como CP437. Algunos
        archivos creados por macOS contienen bytes UTF-8 aunque omiten ese indicador,
        produciendo mojibake como ``compresio╠ün`` o ``├▒`` para ``ñ``. Se intenta
        una recuperación CP437 -> UTF-8 sin pérdida solo cuando aparecen marcadores
        sospechosos o marcas combinantes. Un nombre CP437 legítimo como ``niño``
        no supera la decodificación UTF-8 y permanece intacto.
        """
        name = member.filename if hasattr(member, "filename") else str(member)
        if hasattr(member, "flag_bits") and not (member.flag_bits & 0x800):
            try:
                recovered = name.encode("cp437").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                recovered = None
            if recovered is not None and recovered != name:
                suspicious = any(char in MOJIBAKE_MARKERS for char in name)
                combining = any(unicodedata.combining(char) for char in recovered)
                if suspicious or combining:
                    name = recovered
        normalized = unicodedata.normalize("NFC", name.replace("\\", "/"))
        return "/".join(unicodedata.normalize("NFC", part) for part in normalized.split("/"))

    @staticmethod
    def _is_windows_reserved_component(name: str) -> bool:
        stem = name.rstrip(" .").split(".", 1)[0].upper()
        return stem in {"CON", "PRN", "AUX", "NUL"} or (
            len(stem) == 4 and stem[:3] in {"COM", "LPT"} and stem[3].isdigit() and stem[3] != "0"
        )

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
