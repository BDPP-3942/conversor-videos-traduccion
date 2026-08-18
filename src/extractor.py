from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set
from zipfile import ZipFile

from config import settings


@dataclass
class ExtractionResult:
    """
    Resultado completo de una extracción.
    """

    videos: List[Path] = field(
        default_factory=list
    )

    nested_zips: List[Path] = field(
        default_factory=list
    )

    ignored_files: List[Path] = field(
        default_factory=list
    )

    errors: List[str] = field(
        default_factory=list
    )

    max_depth_reached: int = 0


class ZipExtractor:
    """
    Extrae ZIP y ZIP anidados de forma recursiva.
    """

    def __init__(
        self,
        max_depth: int = settings.MAX_ZIP_DEPTH,
        max_files: int = settings.MAX_EXTRACTED_FILES,
        max_total_size: int = settings.MAX_EXTRACTED_SIZE_BYTES,
    ):
        self.max_depth = max_depth
        self.max_files = max_files
        self.max_total_size = max_total_size

    # ========================================================
    # API PÚBLICA
    # ========================================================

    def extract_zip(
        self,
        zip_path: Path,
        extract_to: Path,
    ) -> ExtractionResult:

        if not zip_path.exists():
            raise FileNotFoundError(
                f"ZIP not found: {zip_path}"
            )

        extract_to.mkdir(
            parents=True,
            exist_ok=True,
        )

        result = ExtractionResult()

        processed_zips: Set[Path] = set()

        self._extract_recursive(
            zip_path=zip_path,
            extract_to=extract_to,
            depth=0,
            result=result,
            processed_zips=processed_zips,
        )

        return result

    # ========================================================
    # RECURSIVIDAD
    # ========================================================

    def _extract_recursive(
        self,
        zip_path: Path,
        extract_to: Path,
        depth: int,
        result: ExtractionResult,
        processed_zips: Set[Path],
    ) -> None:

        if depth > self.max_depth:
            raise ValueError(
                "Maximum ZIP nesting depth exceeded: "
                f"{self.max_depth}"
            )

        zip_path = zip_path.resolve()

        if zip_path in processed_zips:
            return

        processed_zips.add(zip_path)

        result.max_depth_reached = max(
            result.max_depth_reached,
            depth,
        )

        current_dir = (
            extract_to
            / self._safe_directory_name(
                zip_path.stem
            )
        )

        current_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        with ZipFile(zip_path, "r") as archive:

            self._validate_archive(
                archive,
                extract_to=current_dir,
            )

            archive.extractall(current_dir)

        for extracted_path in current_dir.rglob("*"):

            if not extracted_path.is_file():
                continue

            if self._is_ignored(
                extracted_path
            ):
                result.ignored_files.append(
                    extracted_path
                )
                continue

            suffix = (
                extracted_path.suffix.lower()
            )

            if suffix in settings.VIDEO_EXTENSIONS:

                result.videos.append(
                    extracted_path
                )

            elif suffix == ".zip":

                result.nested_zips.append(
                    extracted_path
                )

                self._extract_recursive(
                    zip_path=extracted_path,
                    extract_to=extract_to,
                    depth=depth + 1,
                    result=result,
                    processed_zips=processed_zips,
                )

            else:
                result.ignored_files.append(
                    extracted_path
                )

    # ========================================================
    # VALIDACIÓN ZIP
    # ========================================================

    def _validate_archive(
        self,
        archive: ZipFile,
        extract_to: Path,
    ) -> None:

        total_size = 0
        file_count = 0

        destination = extract_to.resolve()

        for member in archive.infolist():

            filename = member.filename

            if self._is_ignored_name(filename):
                continue

            target = (
                destination / filename
            ).resolve()

            # Protección Zip Slip
            if not target.is_relative_to(
                destination
            ):
                raise ValueError(
                    "Unsafe ZIP path detected: "
                    f"{filename}"
                )

            if member.is_dir():
                continue

            file_count += 1
            total_size += member.file_size

            if file_count > self.max_files:
                raise ValueError(
                    "Maximum number of extracted "
                    f"files exceeded: {self.max_files}"
                )

            if (
                total_size
                > self.max_total_size
            ):
                raise ValueError(
                    "Maximum extracted ZIP size "
                    f"exceeded: "
                    f"{self.max_total_size} bytes"
                )

    # ========================================================
    # FILTROS
    # ========================================================

    @staticmethod
    def _is_ignored(
        path: Path,
    ) -> bool:
        return ZipExtractor._is_ignored_name(
            str(path)
        )

    @staticmethod
    def _is_ignored_name(
        name: str,
    ) -> bool:

        normalized = name.replace(
            "\\",
            "/",
        )

        return (
            normalized.startswith(
                "__MACOSX/"
            )
            or "/__MACOSX/" in normalized
            or normalized.endswith(
                ".DS_Store"
            )
        )

    @staticmethod
    def _safe_directory_name(
        name: str,
    ) -> str:

        invalid_chars = (
            "<>:\"/\\|?*"
        )

        sanitized = "".join(
            "_"
            if char in invalid_chars
            else char
            for char in name
        )

        return (
            sanitized.strip()
            or "archive"
        )