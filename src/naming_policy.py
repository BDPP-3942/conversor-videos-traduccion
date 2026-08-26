from __future__ import annotations

import re
from pathlib import Path

from src.file_naming import SourceNameMetadata, _sanitize_text

_NOISE = re.compile(r"(?:^|[_ .-])(?:wetransfer|drive-download|download|descarga|archive|compressed|backup)(?:[_ .-].*)?$", re.I)
_TIMESTAMP = re.compile(r"\b\d{8}t\d{4,6}z(?:[-_]\d+[-_]\d+)?\b", re.I)
_NUMBER = re.compile(r"(?<!\d)(\d{1,4})(?!\d)")


def _clean(value: str) -> str:
    value = _TIMESTAMP.sub("_", value)
    value = re.sub(r"\s*\((?:copy|copia|\d+)\)\s*$", "", value, flags=re.I)
    value = re.sub(r"[_ .-]+", "_", value).strip("_ .-")
    return value


def _number(value: str) -> int | None:
    value = _clean(value)
    if not value or _NOISE.search(value):
        return None
    match = _NUMBER.search(value)
    return int(match.group(1)) if match else None


def _text(value: str) -> str:
    value = _clean(Path(value).stem)
    value = _NUMBER.sub("_", value)
    value = re.sub(r"(?:^|_)(?:curso|course|leccion|lección|lesson|capitulo|capítulo|chapter|clase|tema|unidad)(?:_|$)", "_", value, flags=re.I)
    value = re.sub(r"_+", "_", value).strip("_")
    return _sanitize_text(value) if value else ""


def resolve(zip_name: str | None, video_name: str) -> SourceNameMetadata:
    """Resolve numbers from container/video and preserve useful non-numeric text.

    Container numbers become course; video numbers become lesson. If neither has a
    useful number, the container text becomes the stable course code and the video
    title becomes the description with no synthetic lesson number.
    """
    zip_text = _text(zip_name) if zip_name else ""
    video_text = _text(video_name)
    course = _number(zip_name or "")
    lesson = _number(video_name)
    if course is None and zip_text:
        course_name = zip_text
    else:
        course_name = None
    if course is None and not zip_text:
        course_name = None
    description = video_text or _sanitize_text(Path(video_name).stem)
    if course is None and lesson is None:
        stem = description
    else:
        prefix = str(course) if course is not None else (course_name or "SIN_CURSO")
        lesson_part = f"{lesson:02d}" if lesson is not None else "SIN_LECCION"
        stem = _sanitize_text(f"{prefix}x{lesson_part}_{description}" if description else f"{prefix}x{lesson_part}")
    return SourceNameMetadata(
        course=course,
        lesson=lesson,
        description=description,
        output_stem=stem,
        confidence="high" if course is not None and lesson is not None else "medium",
        review_required=course is None or lesson is None,
        review_reason="numeric course/lesson not found; preserved useful text" if course is None or lesson is None else None,
        course_name=course_name,
        lesson_name=None,
    )
