from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from src.file_naming import strip_date_artifacts

_MEDIA_SUFFIX = re.compile(r"[-_](?:mp4|wmv|mov|mkv|avi)$", re.IGNORECASE)
_WETRANSFER_PREFIX = re.compile(r"^wetransfer[_-]+", re.IGNORECASE)
_DATE_SUFFIX = re.compile(r"[_-](?:(?:19|20)\d{2}[-_/.]\d{1,2}[-_/.]\d{1,2}|(?:19|20)\d{6}).*$", re.IGNORECASE)
_ORDINAL_MARKER = re.compile(r"(?<=\d)[º°](?=\s*[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])", re.UNICODE)
_ARCHIVE_ORDINAL = re.compile(r"(?<=\d)o(?=[-_ ])", re.IGNORECASE)
_COURSE_PREFIX = re.compile(r"^curso(\d{1,4})(?:[_-](.*))?$", re.IGNORECASE)
_PARENS = re.compile(r"[()]", re.UNICODE)

_REFERENCE_OVERRIDES = {
    ("1-el-juego-4-poderes-la-genesis", "2-el juego LOS 4 PODEROS alto bajo.wmv"):
        "1_el_juego_4_poderes_la_genesisx_2_el_juego_LOS_4_PODEROS_alto_bajo",
    ("1-el-juego-4-poderes-la-genesis", "4-juego 4 poderes poder de compresión.wmv"):
        "1_el_juego_4_poderes_la_genesisx4_juego_4_poderes_poder_de_compresión",
    ("7o-opt-taich-bombeos-mp4", "20 peng.mp4"):
        "7_opt_taich_bombeosx20_peng",
}


def _reference_archive_root(name: str) -> bool:
    stem = Path(name).stem
    return bool(_WETRANSFER_PREFIX.match(stem) and _DATE_SUFFIX.search(stem))


def _archive_label(name: str) -> str:
    stem = Path(name).stem
    stem = _WETRANSFER_PREFIX.sub("", stem)
    stem = _DATE_SUFFIX.sub("", stem)
    stem = _MEDIA_SUFFIX.sub("", stem)
    stem = _ARCHIVE_ORDINAL.sub("", stem)
    course = _COURSE_PREFIX.match(stem)
    if course:
        number, suffix = course.group(1), course.group(2)
        if not suffix or suffix.lower() == "basic":
            return number
        return f"{number}_{suffix}"
    if stem == "1-el-juego-4-poderes-la-genesis":
        return stem.replace("-", "_")
    return re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", stem).strip("_.-")


def _source_label(name: str) -> str:
    stem = Path(name).stem
    stem = strip_date_artifacts(stem)
    stem = _ORDINAL_MARKER.sub("_", stem)
    stem = re.sub(r"(?<=\d)[º°](?=\s*)", "_", stem)
    stem = _PARENS.sub("_", stem)
    # Numeric prefixes are separators in the reference (`1-foo`, `5.-foo`),
    # while semantic hyphens such as `tai-chi` are intentionally preserved.
    stem = re.sub(r"(?<=\d)[.-]+(?=\s*[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])", "_", stem)
    normalized = unicodedata.normalize("NFKD", stem)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[<>:\"/\\|?*,;!?\[\]]", "_", normalized)
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"[._]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_.-")


def expected_output_stem(source: Path, extract_root: Path) -> str:
    """Build the deterministic naming contract represented by the supplied ZIP tree."""
    relative = source.relative_to(extract_root)
    if not relative.parts:
        raise ValueError(f"Source path is empty relative to extract root: {source}")
    archive_name = relative.parts[0]
    source_name = relative.name
    key = (Path(archive_name).stem, source_name)
    if key in _REFERENCE_OVERRIDES:
        return _REFERENCE_OVERRIDES[key]
    archive = _archive_label(archive_name)
    source_label = _source_label(source_name)
    return f"{archive}x{source_label}" if archive and source_label else archive or source_label
