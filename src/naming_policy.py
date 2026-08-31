from __future__ import annotations

import re
from pathlib import Path

from src.file_naming import SourceNameMetadata, _sanitize_text, strip_date_artifacts

_NOISE = re.compile(
    r"(?:wetransfer|drive-download|download|descarga|archive|compressed|backup|compression|extract(?:ed)?|unzip(?:ped)?|descomprim(?:ido|ida|idos|idas))",
    re.IGNORECASE,
)
_COURSE_LABEL = re.compile(r"(?:curso|course)", re.IGNORECASE)
_LESSON_LABEL = re.compile(r"(?:lecci[oó]n|lesson|cap[ií]tulo|chapter|clase|tema|unidad)", re.IGNORECASE)
_COURSE_NUMBER = re.compile(
    r"(?:^|[_\- .])(?:curso|course)\s*[_\-.:#]*\s*(\d{1,4})(?!\d)|\b(\d{1,4})\s*(?:º|°)\s*curso\b", re.IGNORECASE
)
_LESSON_NUMBER = re.compile(
    r"(?:^|[_\- .])(?:cap[ií]tulo|lecci[oó]n|lesson|chapter|clase|tema|unidad)\s*[_\-.:#]*\s*(\d{1,4})(?!\d)|^\s*(\d{1,4})\s*(?:º|°|[._-])\s*",
    re.IGNORECASE,
)
_LEADING_NUMBER = re.compile(r"^\s*(\d{1,4})(?:\s+(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])|[._-])\s*(?:º|°|[._-])?\s*", re.IGNORECASE)
_LOGICAL_LESSON_NUMBER = re.compile(r"(?:^|_)(\d{1,4})(?=_[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])", re.IGNORECASE)
_GENERIC = {
    "mp4",
    "wmv",
    "video",
    "videos",
    "audio",
    "media",
    "file",
    "files",
    "archivo",
    "archivos",
    "download",
    "downloads",
    "descarga",
    "descargas",
    "compressed",
    "compression",
    "archive",
    "zip",
    "rar",
    "7z",
}


def _clean(value: str) -> str:
    value = value.strip()
    suffix = Path(value).suffix.lower()
    if suffix in {".mp4", ".wmv"}:
        value = value[: -len(suffix)]
    value = strip_date_artifacts(value)
    value = re.sub(r"\s*\((?:copy|copia|\d+)\)\s*$", "", value, flags=re.IGNORECASE)
    value = _NOISE.sub("_", value)
    return re.sub(r"[_ .-]+", "_", value).strip("_ .-")


def _clean_context(context_values: list[str]) -> list[str]:
    return [cleaned for part in context_values if (cleaned := _clean(part))]


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
    return next((int(group) for group in match.groups() if group), None)


def _match_source_lesson(source: Path) -> int | None:
    stem = source.name.rsplit(".", 1)[0] if "." in source.name else source.name
    match = _LEADING_NUMBER.match(stem)
    if match:
        return int(match.group(1))
    match = _LESSON_NUMBER.search(stem)
    if match:
        return next((int(group) for group in match.groups() if group), None)
    return None


def _match_logical_lesson(logical_source: Path) -> tuple[int | None, str]:
    stem = _clean(logical_source.stem)
    matches = list(_LOGICAL_LESSON_NUMBER.finditer(stem))
    course_match = _COURSE_NUMBER.search(stem)
    if course_match:
        matches = [match for match in matches if match.start(1) > course_match.end()]
    if not matches:
        return None, ""
    match = matches[-1]
    number = int(match.group(1))
    lesson_fragment = stem[match.start(1) :]
    return number, _description(lesson_fragment, number, _LESSON_LABEL)


def _remove_number(value: str, number: int | None) -> str:
    if number is None:
        return value
    return re.sub(rf"(?<!\d)0*{number}(?!\d)", "_", value, count=1)


def _description(value: str, number: int | None, label_pattern: re.Pattern[str]) -> str:
    cleaned = _clean(value)
    if not cleaned:
        return ""
    cleaned = _remove_number(cleaned, number) if number is not None else cleaned
    cleaned = label_pattern.sub("_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    tokens = [token for token in cleaned.split("_") if token.lower() not in _GENERIC]
    return _sanitize_text("_".join(tokens)) if tokens else ""


def _course_description(value: str, number: int) -> str:
    cleaned = _clean(value)
    match = _COURSE_NUMBER.search(cleaned)
    if not match:
        return ""
    return _description(cleaned[match.end() :], None, _COURSE_LABEL)


def _course_context(context_values: list[str]) -> tuple[int | None, str | None]:
    meaningful = _clean_context(context_values)
    for value in meaningful:
        if _is_noise(value):
            continue
        number = _match_number(value, _COURSE_NUMBER)
        if number is not None:
            return number, _course_description(value, number) or None
    for value in meaningful:
        if _is_noise(value) or _LESSON_LABEL.search(value):
            continue
        return None, _description(value, None, _COURSE_LABEL)
    return None, None


def _lesson_context(
    source: Path, context_values: list[str], logical_source: Path | None = None
) -> tuple[int | None, str]:
    if logical_source is not None:
        number, description = _match_logical_lesson(logical_source)
        if number is not None or description:
            return number, description

    number = _match_source_lesson(source)
    description = _description(source.name, number, _LESSON_LABEL)
    if number is not None or description:
        return number, description

    for value in reversed(_clean_context(context_values)):
        number = _match_number(value, _LESSON_NUMBER)
        description = _description(value, number, _LESSON_LABEL)
        if number is not None or description:
            return number, description
    return None, ""


def resolve(source: Path, extract_root: Path) -> SourceNameMetadata:
    relative = source.relative_to(extract_root)
    raw_parts = list(relative.parts)
    if not raw_parts:
        raise ValueError(f"Source path is empty relative to extract root: {source}")

    logical_relative = "/".join(raw_parts)
    normalized_logical = _clean(logical_relative)
    logical_source = Path(normalized_logical + source.suffix.lower())
    context = _clean_context(raw_parts[:-1])

    course, course_name = _course_context(context)
    lesson, lesson_name = _lesson_context(source, context, logical_source)
    course_part = str(course) if course is not None else (course_name or "")
    if course is not None and course_name:
        course_part = f"{course}_{course_name}"
    lesson_part = f"{lesson:02d}" if lesson is not None else ""
    if lesson_name:
        lesson_part = f"{lesson_part + '_' if lesson_part else ''}{lesson_name}"
    output_stem = "x".join(part for part in (course_part, lesson_part) if part)
    fallback = _sanitize_text(_clean(logical_source.stem))
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
        confidence="high" if course is not None and lesson is not None else "medium",
        review_required=review_required,
        review_reason="; ".join(reasons),
        course_name=course_name,
        lesson_name=lesson_name or None,
    )
