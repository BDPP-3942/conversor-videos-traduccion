from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from zipfile import ZipFile

MEDIA_EXTENSIONS = {".mp4", ".mp3", ".wmv", ".mov", ".mkv", ".avi"}


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
            raise ValueError("ZIP extraction limits must be positive")
        self.max_depth = max_depth
        self.max_files = max_files
        self.max_total_size = max_total_size

    def extract_zip(self, zip_path: Path, extract_to: Path) -> ExtractionResult:
        if not zip_path.is_file():
            raise FileNotFoundError(f"ZIP not found: {zip_path}")
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
            raise ValueError(f"Maximum ZIP nesting depth exceeded: {self.max_depth}")
        if zip_path in processed:
            return
        processed.add(zip_path)
        result.max_depth_reached = max(result.max_depth_reached, depth)

        current_dir = extract_to / self._safe_directory_name(zip_path.stem)
        current_dir.mkdir(parents=True, exist_ok=True)

        with ZipFile(zip_path, "r") as archive:
            members = [m for m in archive.infolist() if not self._is_ignored_name(m.filename)]
            self._validate_archive(members, current_dir, result)
            self._extract_members(archive, members, current_dir)

        for member in members:
            if member.is_dir():
                continue
            extracted_path = (current_dir / member.filename).resolve()
            suffix = extracted_path.suffix.lower()
            if suffix in MEDIA_EXTENSIONS:
                result.media.append(extracted_path)
            elif suffix == ".zip":
                result.nested_zips.append(extracted_path)
                self._extract_recursive(
                    extracted_path,
                    extracted_path.parent,
                    depth + 1,
                    result,
                    processed,
                )
            else:
                result.ignored_files.append(extracted_path)

    def _validate_archive(self, members, destination: Path, result: ExtractionResult) -> None:
        destination = destination.resolve()
        for member in members:
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination):
                raise ValueError(f"Unsafe ZIP path detected: {member.filename}")
            if self._is_symlink(member):
                raise ValueError(f"Symlink entries are not allowed in ZIPs: {member.filename}")
            if member.is_dir():
                continue
            result.extracted_files += 1
            result.extracted_bytes += member.file_size
            if result.extracted_files > self.max_files:
                raise ValueError(f"Maximum number of extracted files exceeded: {self.max_files}")
            if result.extracted_bytes > self.max_total_size:
                raise ValueError(f"Maximum extracted ZIP size exceeded: {self.max_total_size} bytes")

    @staticmethod
    def _extract_members(archive: ZipFile, members, destination: Path) -> None:
        destination = destination.resolve()
        for member in members:
            target = (destination / member.filename).resolve()
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as source, target.open("wb") as output:
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
    def _safe_directory_name(name: str) -> str:
        invalid = '<>:"/\\|?*'
        sanitized = "".join("_" if char in invalid else char for char in name)
        return sanitized.strip() or "archive"
