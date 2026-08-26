from __future__ import annotations

import re
from pathlib import Path

from src.file_naming import SourceNameMetadata, _sanitize_text

_NOISE = re.compile(
    r"(?:wetransfer|drive-download|download|descarga|archive|compressed|backup|compression|"
    r"extract(?:ed)?|unzip(?:ped)?|descomprim(?:ido|ida|idos|idas))",
    re.IGNORECASE,
)
_TIMESTAMP = re.compile(r"\b\d{8}t\d{4,6}z(?:[-_]\d+[-_]\d+)?\b", re.IGNORECASE)
_NUMBER = re.compile(r"(?<!\d)(\d{1,4})(?!\d)")
_LABEL = re.compile(
    r"(?:curso|course|lecci[oó]n|lesson|cap[ií]tulo|chapter|clase|tema|unidad)",
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


def _number(value: str) -> int | None:
    cleaned = _clean(value)
    if not cleaned or _TIMESTAMP.search(value) or _is_noise(cleaned):
        return None
    match = _NUMBER.search(cleaned)
    return int(match.group(1)) if match else None


def _description(video_name: str, lesson: int | None) -> str:
    value = _clean(video_name)
    if lesson is not None:
        value = _NUMBER.sub("_", value, count=1)
    value = _LABEL.sub("_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    tokens = [token for token in value.split("_") if token.lower() not in _GENERIC]
    return _sanitize_text("_".join(tokens)) if tokens else ""


def _course_code(context_values: list[str]) -> str | None:
    for value in context_values:
        cleaned = _clean(value)
        if _is_noise(cleaned):
            continue
        without_numbers = _NUMBER.sub("_", cleaned)
        without_labels = _LABEL.sub("_", without_numbers)
        tokens = [token for token in re.split(r"_+", without_labels) if token]
        tokens = [token for token in tokens if token.lower() not in _GENERIC]
        if tokens:
            return _sanitize_text("_".join(tokens))
    return None


def resolve(source: Path, extract_root: Path) -> SourceNameMetadata:
    """Apply one naming policy to ZIP, raw-video and migration flows."""
    relative = source.relative_to(extract_root)
    context = list(relative.parts[:-1])
    course = next((value for value in (_number(item) for item in context) if value is not None), None)
    lesson = _number(source.name)
    course_name = None if course is not None else _course_code(context)
    description = _description(source.name, lesson)

    if course is not None and lesson is not None:
        output_stem = f"{course}x{lesson:02d}"
    elif course is not None:
        output_stem = str(course)
    elif course_name:
        output_stem = course_name
    else:
        output_stem = ""
    if description:
        output_stem = f"{output_stem}_{description}" if output_stem else description

    review_required = course is None or lesson is None
    reasons = []
    if course is None:
        reasons.append("course number not found; textual code inferred when possible")
    if lesson is None:
        reasons.append("lesson number not found; no synthetic lesson number added")
    return SourceNameMetadata(
        course=course,
        lesson=lesson,
        description=description or _sanitize_text(source.stem),
        output_stem=output_stem or _sanitize_text(source.stem),
        confidence="high" if course is not None and lesson is not None else "medium",
        review_required=review_required,
        review_reason="; ".join(reasons),
        course_name=course_name,
        lesson_name=None,
    )
