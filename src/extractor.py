from __future__ import annotations

import unicodedata
import zipfile
from pathlib import Path

# Marcadores conservadores de nombres que suelen aparecer cuando bytes UTF-8
# se interpretan como CP437 sin el indicador UTF-8 del ZIP.
MOJIBAKE_MARKERS = frozenset("╠╣╚╝├┤┴┬ÃÂ")


class ZipExtractor:
    """Extrae ZIP de forma segura y repara nombres Unicode mal decodificados."""

    @staticmethod
    def _decode_member_name(member: zipfile.ZipInfo | str) -> str:
        """Recupera un nombre UTF-8 mal decodificado y lo normaliza a NFC."""
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
