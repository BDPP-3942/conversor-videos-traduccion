import re
from pathlib import Path


class FileNameFormatter:

    LANGUAGE_PATTERN = re.compile(
        r"(?P<separator>[_\-.])"
        r"(?P<lang>es|en|es-es|en-us)"
        r"(?P<extension>\.[^.]+)$",
        re.IGNORECASE,
    )

    @classmethod
    def parse(cls, filename: str) -> dict:
        path = Path(filename)

        match = cls.LANGUAGE_PATTERN.search(path.name)

        if not match:
            return {
                "original_name": path.name,
                "stem": path.stem,
                "language": None,
                "extension": path.suffix.lower(),
            }

        return {
            "original_name": path.name,
            "stem": path.stem[
                :match.start()
            ],
            "language": match.group("lang").lower(),
            "extension": path.suffix.lower(),
        }

    @classmethod
    def translated_vtt_name(
        cls,
        mp4_path: Path,
        target_language: str,
    ) -> str:

        info = cls.parse(mp4_path.name)

        base_name = info["stem"]

        return (
            f"{base_name}_"
            f"{target_language.lower()}.vtt"
        )