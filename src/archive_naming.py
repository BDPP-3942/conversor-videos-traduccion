from __future__ import annotations

import re
from pathlib import Path

from src.file_naming import clean_for_filename, strip_date_artifacts

_MEDIA_SUFFIX = re.compile(r"[-_](?:mp4|wmv|mov|mkv|avi)$", re.IGNORECASE)
_WETRANSFER_PREFIX = re.compile(r"^wetransfer[_-]+", re.IGNORECASE)
_DATE_SUFFIX = re.compile(
    r"[_-](?:(?:19|20)\d{2}[-_/.]\d{1,2}[-_/.]\d{1,2}"
    r"|(?:19|20)\d{6}).*$",
    re.IGNORECASE,
)
_ORDINAL_MARKER = re.compile(
    r"(?<=\d)[º°](?=\s*[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])",
    re.UNICODE,
)
_ARCHIVE_ORDINAL = re.compile(r"(?<=\d)o(?=[-_ ])", re.IGNORECASE)
_COURSE_PREFIX = re.compile(r"^curso(\d{1,4})(?:[_-](.*))?$", re.IGNORECASE)
_PARENS = re.compile(r"[()]", re.UNICODE)
_LEADING_NUMBER_SEPARATOR = re.compile(r"^(\d{1,4})[_-]+(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])")


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
        return clean_for_filename(f"{number}_{suffix}")
    return clean_for_filename(stem)


def _source_label(name: str) -> str:
    stem = Path(name).stem
    stem = strip_date_artifacts(stem)
    stem = _ORDINAL_MARKER.sub("_", stem)
    stem = re.sub(r"(?<=\d)[º°](?=\s*)", "_", stem)
    stem = _PARENS.sub("_", stem)
    stem = re.sub(
        r"(?<=\d)[.-]+(?=\s*[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])",
        "_",
        stem,
    )
    normalized = clean_for_filename(stem)
    return _LEADING_NUMBER_SEPARATOR.sub(r"\1", normalized)


def expected_output_stem(source: Path, extract_root: Path) -> str:
    """Build the deterministic naming contract represented by the supplied ZIP tree."""
    relative = source.relative_to(extract_root)
    if not relative.parts:
        raise ValueError(f"Source path is empty relative to extract root: {source}")
    archive_name = relative.parts[0]
    source_name = relative.name
    archive = _archive_label(archive_name)
    source_label = _source_label(source_name)
    if archive and source_label:
        return f"{archive}x{source_label}"
    return archive or source_label
