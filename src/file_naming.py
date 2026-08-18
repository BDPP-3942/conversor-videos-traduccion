import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FileNameInfo:
    """
    Información inferida del nombre del archivo.
    """

    original_name: str
    stem: str
    extension: str
    language: Optional[str] = None


class FileNameFormatter:
    """
    Normaliza y genera nombres relacionados con los vídeos
    y sus subtítulos.
    """

    LANGUAGE_PATTERN = re.compile(
        r"(?P<separator>[_\-.])"
        r"(?P<language>"
        r"es|en|es-es|en-us"
        r")"
        r"(?P<extension>\.[^.]+)$",
        re.IGNORECASE,
    )

    # ========================================================
    # ANALIZAR
    # ========================================================

    @classmethod
    def parse(
        cls,
        filename: str,
    ) -> FileNameInfo:

        path = Path(filename)

        match = cls.LANGUAGE_PATTERN.search(
            path.name
        )

        if not match:
            return FileNameInfo(
                original_name=path.name,
                stem=path.stem,
                extension=path.suffix.lower(),
            )

        base_stem = path.stem[
            :match.start()
        ]

        return FileNameInfo(
            original_name=path.name,
            stem=base_stem,
            extension=path.suffix.lower(),
            language=match.group(
                "language"
            ).lower(),
        )

    # ========================================================
    # GENERAR VTT
    # ========================================================

    @classmethod
    def generate_vtt_name(
        cls,
        video_filename: str,
        target_language: str,
    ) -> str:

        info = cls.parse(
            video_filename
        )

        language = (
            target_language.lower()
        )

        return (
            f"{info.stem}_"
            f"{language}.vtt"
        )

    # ========================================================
    # NORMALIZAR VIDEO
    # ========================================================

    @staticmethod
    def normalize_video_name(
        filename: str,
    ) -> str:

        path = Path(filename)

        # Espacios múltiples
        name = re.sub(
            r"\s+",
            " ",
            path.stem.strip(),
        )

        # Caracteres problemáticos
        name = re.sub(
            r'[<>:"/\\|?*]',
            "_",
            name,
        )

        return (
            f"{name}"
            f"{path.suffix.lower()}"
        )
    