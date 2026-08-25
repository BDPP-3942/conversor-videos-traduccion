from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from src.path_limits import _WINDOWS_RESERVED, fit_component


@dataclass(frozen=True)
class FileNameInfo:
    original_name: str
    stem: str
    extension: str
    language: str | None = None


@dataclass(frozen=True)
class SourceNameMetadata:
    course: int | None
    lesson: int | None
    description: str
    output_stem: str
    confidence: str
    review_required: bool
    review_reason: str | None
    course_name: str | None = None
    lesson_name: str | None = None


class FileNameFormatter:
    """Infer course/lesson labels and build stable WordPress-friendly output names."""

    LANGUAGE_PATTERN = re.compile(
        r"(?P<separator>[_\-.])(?P<language>es|en|es-es|en-us)(?P<extension>\.[^.]+)$",
        re.IGNORECASE,
    )
    COURSE_PATTERNS = (
        re.compile(r"(?:^|[_\- .])(?:curso|course)\s*[_\-.:#]*\s*(\d{1,4})(?!\d)", re.IGNORECASE),
        re.compile(r"\b(\d{1,4})\s*(?:º|°)\s*curso\b", re.IGNORECASE),
    )
    LESSON_PATTERNS = (
        re.compile(
            r"(?:^|[_\- .])(?:cap[ií]tulo|lecci[oó]n|lesson|chapter|clase|tema|unidad)\s*[_\-.:#]*\s*(\d{1,4})\b",
            re.IGNORECASE,
        ),
        re.compile(r"^\s*(\d{1,4})\s*(?:º|°|[._-])\s*", re.IGNORECASE),
    )
    COURSE_TEXT_PATTERNS = (
        re.compile(r"\b(?:curso|course)\s*[:\-–—.]?\s*([^|/\\]+)", re.IGNORECASE),
    )
    LESSON_TEXT_PATTERNS = (
        re.compile(
            r"\b(?:lecci[oó]n|lesson|cap[ií]tulo|chapter|clase|tema|unidad)\s*[:\-–—.]?\s*([^|/\\]+)",
            re.IGNORECASE,
        ),
    )

    # Prefixes/suffixes frequently produced by download/compression services.
    NOISE_PATTERNS = (
        re.compile(r"^wetransfer[_\-]+", re.IGNORECASE),
        re.compile(r"^drive-download[-_][0-9tz\-]+(?:[-_]\d+[-_]\d+)?[-_]", re.IGNORECASE),
        re.compile(r"^(?:zip|rar|7z|archive|compressed|compression|backup|download|descarga)[-_ ]+", re.IGNORECASE),
        re.compile(r"^(?:extract(?:ed)?|unzip(?:ped)?|descomprim(?:ido|ida|idos|idas))[-_ ]+", re.IGNORECASE),
        re.compile(r"^files?[-_ ]+(?:from|de)[-_ ]+", re.IGNORECASE),
        re.compile(r"\s*\((?:copy|copia|\d+)\)\s*$", re.IGNORECASE),
        re.compile(r"[_\-]+copy\s*$", re.IGNORECASE),
    )
    GENERIC_TOKENS = {
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
        "archivo_comprimido",
        "zip",
        "rar",
        "7z",
    }
    FILENAME_ARTIFACT_PATTERN = re.compile(
        r"(?:^|[_\- .])(?:\d{8}t\d{4,6}z(?:[-_]\d+[-_]\d+)?)(?:[_\- .]|$)", re.IGNORECASE
    )

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
        return normalize_filename(filename)

    @classmethod
    def resolve_source_metadata(cls, source: Path, extract_root: Path) -> SourceNameMetadata:
        relative = source.relative_to(extract_root)
        parts = list(relative.parts)
        context_values = parts[:-1]
        stem = source.stem

        cleaned_parts = [cls._clean_context(value) for value in context_values]
        cleaned_stem = cls._clean_context(stem)
        combined_context = " / ".join([value for value in cleaned_parts if value])

        course = cls._find_course(context_values + [stem])
        lesson = cls._find_lesson(stem)
        if lesson is None:
            lesson = cls._find_lesson(" ".join(context_values))

        course_name = cls._find_course_name(context_values + [stem])
        if course_name is None:
            course_name = cls._infer_context_course_name(context_values[:1])
        lesson_name = cls._find_lesson_name([stem] + context_values)
        if lesson_name is None and lesson is None:
            lesson_name = cls._infer_context_lesson_name(context_values)

        # Numeric values always win over textual guesses.
        if course is not None:
            course_name = None
        if lesson is not None:
            lesson_name = None

        description = cls._build_description(
            cleaned_stem,
            course=course,
            lesson=lesson,
            course_name=course_name,
            lesson_name=lesson_name,
        )

        inferred_labels = sum(value is not None for value in (course_name, lesson_name))
        if course is not None and lesson is not None:
            confidence = "high"
        elif course is not None or lesson is not None:
            confidence = "medium"
        elif inferred_labels:
            confidence = "medium-low"
        else:
            confidence = "low"

        review_required = course is None or lesson is None
        reasons = []
        if course is None and course_name is None:
            reasons.append("course was not confidently inferred from source tree")
        elif course is None and course_name is not None:
            reasons.append("course name inferred from explicit text marker")
        if lesson is None and lesson_name is None:
            reasons.append("lesson was not confidently inferred from source tree")
        elif lesson is None and lesson_name is not None:
            reasons.append("lesson name inferred from explicit text marker")
        if combined_context and any(cls._looks_like_download_artifact(value) for value in context_values):
            reasons.append("download/compression naming noise was ignored")

        course_text = str(course) if course is not None else cls._label_or_default(course_name, "SIN_CURSO")
        lesson_text = f"{lesson:02d}" if lesson is not None else cls._label_or_default(lesson_name, "SIN_LECCION")
        label_prefix = f"{course_text}x{lesson_text}"
        description_key = _sanitize_text(description).lower()
        lesson_key = _sanitize_text(lesson_name or "").lower()
        if lesson_name and description_key == lesson_key:
            output_stem = label_prefix
        elif description:
            output_stem = _sanitize_text(f"{label_prefix}_{description}")
        else:
            output_stem = label_prefix

        return SourceNameMetadata(
            course=course,
            lesson=lesson,
            description=description,
            output_stem=output_stem,
            confidence=confidence,
            review_required=review_required,
            review_reason="; ".join(reasons) if reasons else None,
            course_name=course_name,
            lesson_name=lesson_name,
        )

    @classmethod
    def _find_course(cls, parts: list[str]) -> int | None:
        for value in parts:
            for pattern in cls.COURSE_PATTERNS:
                match = pattern.search(value)
                if match:
                    return int(match.group(1))
        return None

    @classmethod
    def _find_lesson(cls, value: str) -> int | None:
        for pattern in cls.LESSON_PATTERNS:
            match = pattern.search(value)
            if match:
                return int(match.group(1))
        return None

    @classmethod
    def _find_course_name(cls, values: list[str]) -> str | None:
        # Only infer free-text course names when an explicit "curso/course" marker exists.
        for value in values:
            cleaned = cls._clean_context(value)
            for pattern in cls.COURSE_TEXT_PATTERNS:
                match = pattern.search(cleaned)
                if not match:
                    continue
                candidate = cls._clean_label(match.group(1))
                if candidate and not candidate.isdigit() and not cls._is_generic_label(candidate):
                    return candidate
        return None

    @classmethod
    def _infer_context_course_name(cls, values: list[str]) -> str | None:
        for value in values:
            if cls._looks_like_download_artifact(value):
                continue
            cleaned = cls._clean_context(value)
            candidate = cls._clean_label(cleaned)
            if not candidate or cls._is_generic_label(candidate):
                continue
            if cls._find_lesson(cleaned) is not None or cls._find_course(cleaned) is not None:
                if re.search(r"\b(?:curso|course)\b", cleaned, re.IGNORECASE):
                    continue
            return candidate
        return None

    @classmethod
    def _infer_context_lesson_name(cls, values: list[str]) -> str | None:
        for value in reversed(values):
            if cls._looks_like_download_artifact(value):
                continue
            cleaned = cls._clean_context(value)
            candidate = cls._clean_label(cleaned)
            if not candidate or cls._is_generic_label(candidate):
                continue
            return candidate
        return None

    @classmethod
    def _find_lesson_name(cls, values: list[str]) -> str | None:
        # Prefer explicit semantic markers. This avoids interpreting arbitrary text as a lesson.
        for value in values:
            cleaned = cls._clean_context(value)
            for pattern in cls.LESSON_TEXT_PATTERNS:
                match = pattern.search(cleaned)
                if not match:
                    continue
                candidate = cls._clean_label(match.group(1))
                if candidate and not candidate.isdigit() and not cls._is_generic_label(candidate):
                    return candidate
        return None

    @classmethod
    def _build_description(
        cls,
        stem: str,
        course: int | None,
        lesson: int | None,
        course_name: str | None,
        lesson_name: str | None,
    ) -> str:
        description = cls._clean_context(stem)
        for pattern in cls.LESSON_PATTERNS:
            description = pattern.sub("", description, count=1)
        for pattern in cls.LESSON_TEXT_PATTERNS:
            description = pattern.sub("", description, count=1)
        if course is not None:
            for pattern in cls.COURSE_PATTERNS:
                description = pattern.sub("", description, count=1)
        if course_name:
            for pattern in cls.COURSE_TEXT_PATTERNS:
                description = pattern.sub("", description, count=1)
        if lesson_name:
            # Do not strip the entire description if the same words are part of a useful title.
            description = re.sub(r"\s+", " ", description).strip()
        description = re.sub(r"[_\- ]+", "_", description)
        description = cls._remove_generic_tokens(description)
        if not description:
            description = lesson_name or course_name or "SIN_NOMBRE"
        return _sanitize_text(description)

    @classmethod
    def _clean_context(cls, value: str) -> str:
        cleaned = value.replace("\\", "/").strip()
        cleaned = cls.FILENAME_ARTIFACT_PATTERN.sub("_", cleaned)
        for pattern in cls.NOISE_PATTERNS:
            cleaned = pattern.sub("", cleaned)
        cleaned = re.sub(r"(?:[_\- ]){2,}", "_", cleaned).strip(" _-.\t")
        return cleaned

    @classmethod
    def _clean_label(cls, value: str) -> str:
        value = cls._clean_context(value)
        value = re.sub(
            r"\b(?:curso|course|lecci[oó]n|lesson|cap[ií]tulo|chapter|clase|tema)\b",
            "",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(r"\b\d{1,4}\b", "", value)
        value = re.sub(r"[_\-]+", " ", value)
        value = re.sub(r"\s+", " ", value).strip(" ._-:;,")
        return value

    @classmethod
    def _remove_generic_tokens(cls, value: str) -> str:
        tokens = [token for token in re.split(r"[_ ]+", value) if token]
        filtered = [token for token in tokens if token.lower() not in cls.GENERIC_TOKENS]
        return "_".join(filtered)

    @classmethod
    def _is_generic_label(cls, value: str) -> bool:
        compact = re.sub(r"[_ ]+", " ", value).strip().lower()
        return compact in cls.GENERIC_TOKENS or not re.search(r"[a-záéíóúüñ]", compact, re.IGNORECASE)

    @classmethod
    def _looks_like_download_artifact(cls, value: str) -> bool:
        lowered = value.lower()
        return (
            lowered.startswith(("wetransfer_", "drive-download-", "zip-", "archive-", "compressed-"))
            or bool(cls.FILENAME_ARTIFACT_PATTERN.search(value))
        )

    @classmethod
    def comparison_key(cls, filename: str) -> str:
        """Normalize a media title for duplicate-candidate matching.

        The comparison key removes transport/download noise but intentionally keeps
        meaningful numeric prefixes such as lesson numbers.
        """
        path = Path(filename)
        value = cls._clean_context(path.stem)
        value = re.sub(
            r"(?:[_\- .]+)(?:20\d{2}[-_](?:0?[1-9]|1[0-2])[-_](?:0?[1-9]|[12]\d|3[01])[_-]\d{4,6})(?:[-_]\d+)?$",
            "",
            value,
            flags=re.IGNORECASE,
        )
        value = cls._remove_generic_tokens(value)
        value = re.sub(r"[^a-zA-Z0-9]+", " ", _sanitize_text(value)).lower().strip()
        return re.sub(r"\s+", " ", value)

    @classmethod
    def normalized_title(cls, filename: str) -> str:
        return cls.comparison_key(filename)

    @staticmethod
    def _label_or_default(value: str | None, default: str) -> str:
        if not value:
            return default
        return _sanitize_text(value.replace(" ", "_"))


def normalize_comparison_key(filename: str) -> str:
    return FileNameFormatter.comparison_key(filename)


def normalized_name_similarity(left: str, right: str) -> float:
    from difflib import SequenceMatcher

    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    sequence_score = SequenceMatcher(None, left, right).ratio()
    union = left_tokens | right_tokens
    token_score = len(left_tokens & right_tokens) / len(union) if union else 0.0
    return 0.65 * sequence_score + 0.35 * token_score


def normalize_filename(filename: str) -> str:
    """Normalize a filename while preserving its extension.
    ``filename`` is a filename value, not a filesystem path. On Windows,
    ``pathlib.Path`` interprets a colon in a value such as ``"a:b.mp4"`` as
    a drive designator and would therefore discard the ``"a:"`` portion.
    Split path separators explicitly instead so invalid Windows characters
    are sanitized rather than reinterpreted as path syntax.
    """
    basename = re.split(r"[\\/]", filename)[-1]
    if not basename:
        return "SIN_NOMBRE"
    if "." in basename and not basename.startswith("."):
        stem, extension = basename.rsplit(".", 1)
        extension = f".{extension.lower()}"
    else:
        stem, extension = basename, ""
    return f"{_sanitize_text(stem)}{extension}"


def normalize_component(value: str) -> str:
    """Normalize one directory/file component using the WordPress-friendly policy."""
    return _sanitize_text(value)


def _sanitize_text(value: str) -> str:
    """Generate ASCII-friendly filenames compatible with WordPress and common filesystems."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    safe: list[str] = []
    for char in ascii_text:
        if char.isalnum() or char in "._-":
            safe.append(char)
        elif char.isspace() or char in '<>:/\\|?*\";,&$#()[]{}%+!~`' or ord(char) < 32:
            safe.append("_")
        else:
            safe.append("_")
    result = re.sub(r"_+", "_", "".join(safe)).strip(" ._-")
    if not result:
        return "SIN_NOMBRE"
    if _WINDOWS_RESERVED.match(result):
        result = f"_{result}"
    return result


def fit_output_stem(
    stem: str,
    parent: Path,
    unique_suffix: str | None = None,
    reserve_suffixes: tuple[str, ...] = (),
) -> str:
    """Fit a shared output stem while reserving room for generated artifact suffixes."""
    suffix = f"__{unique_suffix}" if unique_suffix else ""
    candidate = fit_component(stem, parent, suffix=suffix)
    if not reserve_suffixes:
        return candidate

    from src.path_limits import get_filesystem_limits

    limits = get_filesystem_limits(parent)
    max_component = max(1, limits.max_component)
    extra = max((len(item.encode("utf-8")) for item in reserve_suffixes), default=0)
    current = candidate.encode("utf-8")
    allowed = max(1, max_component - extra)
    if len(current) <= allowed:
        return candidate
    raw = candidate.encode("utf-8")[:allowed]
    while raw:
        try:
            prefix = raw.decode("utf-8").rstrip(" ._-")
            if prefix:
                return prefix
        except UnicodeDecodeError:
            raw = raw[:-1]
            continue
        raw = raw[:-1]
    return "_"
