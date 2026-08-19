import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class FileNameInfo:
    original_name: str
    stem: str
    extension: str
    language: Optional[str] = None


@dataclass(frozen=True)
class SourceNameMetadata:
    course: Optional[int]
    lesson: Optional[int]
    description: str
    output_stem: str
    confidence: str
    review_required: bool
    review_reason: Optional[str]


class FileNameFormatter:
    """Genera nombres estables y trazables a partir del árbol de origen."""

    LANGUAGE_PATTERN = re.compile(
        r"(?P<separator>[_\-.])(?P<language>es|en|es-es|en-us)(?P<extension>\.[^.]+)$",
        re.IGNORECASE,
    )
    COURSE_PATTERNS = (
        re.compile(r"(?:curso|course)[ _.-]?(\d+)", re.IGNORECASE),
        re.compile(r"\b(\d+)\s*(?:º|°)\s*curso\b", re.IGNORECASE),
    )
    LESSON_PATTERNS = (
        re.compile(r"(?:cap[ií]tulo|lecci[oó]n|lesson|chapter)[ _.-]?(\d+)", re.IGNORECASE),
        re.compile(r"^\s*(\d+)\s*(?:º|°|[._-])\s*", re.IGNORECASE),
    )
    COURSE_TOKEN_PATTERN = re.compile(r"\bcurso\s*\d+\b", re.IGNORECASE)

    @classmethod
    def parse(cls, filename: str) -> FileNameInfo:
        path = Path(filename)
        match = cls.LANGUAGE_PATTERN.search(path.name)
        if not match:
            return FileNameInfo(path.name, path.stem, path.suffix.lower())
        return FileNameInfo(
            original_name=path.name,
            stem=path.stem[: match.start()],
            extension=path.suffix.lower(),
            language=match.group("language").lower(),
        )

    @classmethod
    def generate_vtt_name(cls, video_filename: str, target_language: str) -> str:
        info = cls.parse(video_filename)
        return f"{info.stem}_{target_language.lower()}.vtt"

    @staticmethod
    def normalize_video_name(filename: str) -> str:
        path = Path(filename)
        return f"{_sanitize_text(path.stem)}{path.suffix.lower()}"

    @classmethod
    def resolve_source_metadata(cls, source: Path, extract_root: Path) -> SourceNameMetadata:
        relative = source.relative_to(extract_root)
        parts = list(relative.parts)
        stem = source.stem

        course = cls._find_course(parts)
        lesson = cls._find_lesson(stem)
        if lesson is None:
            lesson = cls._find_lesson(" ".join(parts[:-1]))

        description = cls._build_description(stem, course=course, lesson=lesson)
        confidence = (
            "high"
            if course is not None and lesson is not None
            else "medium"
            if course is not None
            else "low"
        )
        review_required = course is None or lesson is None
        reasons = []
        if course is None:
            reasons.append("course number not confidently inferred from source tree")
        if lesson is None:
            reasons.append("lesson/chapter number not confidently inferred from source tree")

        course_text = str(course) if course is not None else "SIN_CURSO"
        lesson_text = f"{lesson:02d}" if lesson is not None else "SIN_LECCION"
        output_stem = _sanitize_text(f"{course_text}x{lesson_text}_{description}")

        return SourceNameMetadata(
            course=course,
            lesson=lesson,
            description=description,
            output_stem=output_stem,
            confidence=confidence,
            review_required=review_required,
            review_reason="; ".join(reasons) if reasons else None,
        )

    @classmethod
    def _find_course(cls, parts: list[str]) -> Optional[int]:
        for value in parts:
            for pattern in cls.COURSE_PATTERNS:
                match = pattern.search(value)
                if match:
                    return int(match.group(1))
        return None

    @classmethod
    def _find_lesson(cls, value: str) -> Optional[int]:
        for pattern in cls.LESSON_PATTERNS:
            match = pattern.search(value)
            if match:
                return int(match.group(1))
        return None

    @classmethod
    def _build_description(cls, stem: str, course: Optional[int], lesson: Optional[int]) -> str:
        description = stem
        for pattern in cls.LESSON_PATTERNS:
            description = pattern.sub("", description, count=1)
        if course is not None:
            description = cls.COURSE_TOKEN_PATTERN.sub("", description)
        description = description.replace("-", " ").replace("_", " ")
        return _sanitize_text(description)


def _sanitize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_like = "".join(char for char in normalized if not unicodedata.combining(char))
    ascii_like = ascii_like.replace("\u00ba", " ").replace("\u00b0", " ")
    ascii_like = re.sub(r"[^A-Za-z0-9]+", "_", ascii_like)
    return re.sub(r"_+", "_", ascii_like).strip("_") or "SIN_NOMBRE"
