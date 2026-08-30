from __future__ import annotations

import re
from pathlib import Path

from src.file_naming import SourceNameMetadata, _sanitize_text

_NOISE = re.compile(
    r"(?:wetransfer|drive-download|download|descarga|archive|compressed|backup|compression|"
    r"extract(?:ed)?|unzip(?:ped)?|descomprim(?:ido|ida|idos|idas))",
    re.IGNORECASE,
)
# Transport/download tools commonly append timestamps in several conventions.
# Keep these patterns deliberately date-specific so course/lesson numbers are not
# accidentally discarded as generic numeric noise.
_DATE = re.compile(
    r"(?:"
    r"\b\d{8}t\d{4,6}z(?:[-_]\d+[-_]\d+)?\b|"
    r"\b\d{8}[ _-]?\d{4,6}\b|"
    r"\b\d{4}[-_.]\d{1,2}[-_.]\d{1,2}(?:[ _T-]+\d{1,2}[-:.]\d{2}(?:[-:.]\d{2})?)?\b|"
    r"\b\d{1,2}[-_.]\d{1,2}[-_.]\d{4}(?:[ _T-]+\d{1,2}[-:.]\d{2}(?:[-:.]\d{2})?)?\b|"
    r"\b\d{4}[-_.]\d{1,2}[-_.]\d{1,2}[T _-]\d{1,2}[-:.]\d{2}(?:[-:.]\d{2})?(?:Z|[+-]\d{2}:?\d{2})?\b"
    r")",
    re.IGNORECASE,
)
_TIMESTAMP = _DATE
_NUMBER = re.compile(r"(?<!\d)(\d{1,4})(?!\d)")
_COURSE_LABEL = re.compile(r"(?:curso|course)", re.IGNORECASE)
_LESSON_LABEL = re.compile(r"(?:lecci[oó]n|lesson|cap[ií]tulo|chapter|clase|tema|unidad)", re.IGNORECASE)
_COURSE_NUMBER = re.compile(
    r"(?:^|[_\- .])(?:curso|course)\s*[_\-.:#]*\s*(\d{1,4})(?!\d)|"
    r"\b(\d{1,4})\s*(?:º|°)\s*curso\b",
    re.IGNORECASE,
)
_LESSON_NUMBER = re.compile(
    r"(?:^|[_\- .])(?:cap[ií]tulo|lecci[oó]n|lesson|chapter|clase|tema|unidad)\s*[_\-.:#]*\s*(\d{1,4})(?!\d)|"
    r"^\s*(\d{1,4})\s*(?:º|°|[._-])\s*",
    re.IGNORECASE,
)
_GENERIC = {
    "mp4", "wmv", "video", "videos", "audio", "media", "file", "files",
    "archivo", "archivos", "download", "downloads", "descarga", "descargas",
    "compressed", "compression", "archive", "zip", "rar", "7z",
}


def _clean(value: str) -> str:
    value = Path(value).stem
    value = _TIMESTAMP.sub("_", value)
    value = re.sub(r"\s*\((?:copy|copia|\d+)\)\s*$", "", value, flags=re.IGNORECASE)
    value = _NOISE.sub("_", value)
    return re.sub(r"[_ .-]+", "_", value).strip("_ .-")


def _is_noise(value: str) -> bool:
    cleaned = _clean(value).lower()
    return not cleaned or cleaned in _GENERIC or not re.search(r"[a-záéíóúüñ]", cleaned)


def _match_number(value: str, pattern: re.Pattern[str]) -> int | None:
    cleaned = _clean(value)
    if not cleaned or _is_noise(cleaned):
        return None
    match = pattern.search(cleaned)
    if not match:
        return None
    for group in match.groups():
        if group:
            return int(group)
    return None


def _remove_number(value: str, number: int | None) -> str:
    if number is None:
        return value
    return re.sub(rf"(?<!\d)0*{number}(?!\d)", "_", value, count=1)


def _description(value: str, number: int | None, label_pattern: re.Pattern[str]) -> str:
    cleaned = _clean(value)
    if not cleaned:
        return ""
    if number is not None:
        cleaned = _remove_number(cleaned, number)
    cleaned = label_pattern.sub("_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    tokens = [token for token in cleaned.split("_") if token.lower() not in _GENERIC]
    return _sanitize_text("_".join(tokens)) if tokens else ""


def _course_context(context_values: list[str]) -> tuple[int | None, str | None]:
    """Find course number and description from the same meaningful path component."""
    for value in context_values:
        number = _match_number(value, _COURSE_NUMBER)
        if number is not None:
            return number, _description(value, number, _COURSE_LABEL)
    for value in context_values:
        number = _match_number(value, _NUMBER)
        if number is not None and not _LESSON_LABEL.search(value):
            return number, _description(value, number, _COURSE_LABEL)
    for value in context_values:
        cleaned = _clean(value)
        if not _is_noise(cleaned):
            return None, _description(cleaned, None, _COURSE_LABEL)
    return None, None


def _lesson_context(source: Path, context_values: list[str]) -> tuple[int | None, str]:
    """Find lesson number/description from filename, then its immediate parent context."""
    number = _match_number(source.name, _LESSON_NUMBER)
    description = _description(source.name, number, _LESSON_LABEL)
    if number is not None or description:
        return number, description
    for value in reversed(context_values):
        number = _match_number(value, _LESSON_NUMBER)
        description = _description(value, number, _LESSON_LABEL)
        if number is not None or description:
            return number, description
    return None, ""


def resolve(source: Path, extract_root: Path) -> SourceNameMetadata:
    """Build stable names such as ``12_movilidad_articularx03_rotacion_hombros``."""
    relative = source.relative_to(extract_root)
    context = list(relative.parts[:-1])
    course, course_name = _course_context(context)
    lesson, lesson_name = _lesson_context(source, context)
    course_part = str(course) if course is not None else (course_name or "")
    if course is not None and course_name:
        course_part = f"{course}_{course_name}"
    lesson_part = f"{lesson:02d}" if lesson is not None else ""
    if lesson_name:
        lesson_part = f"{lesson_part + '_' if lesson_part else ''}{lesson_name}"
    output_stem = "x".join(part for part in (course_part, lesson_part) if part)
    fallback = _sanitize_text(_clean(source.stem))
    output_stem = output_stem or fallback
    review_required = course is None or lesson is None
    reasons: list[str] = []
    if course is None:
        reasons.append("course number not found; textual course description used when available")
    if lesson is None:
        reasons.append("lesson number not found; textual lesson description used when available")
    return SourceNameMetadata(
        course=course,
        lesson=lesson,
        description=lesson_name or course_name or fallback,
        output_stem=output_stem,
        confidence=("high" if course is not None and lesson is not None else "medium"),
        review_required=review_required,
        review_reason="; ".join(reasons),
        course_name=course_name,
        lesson_name=lesson_name or None,
    )
