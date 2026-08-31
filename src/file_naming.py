from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

from src.path_limits import fit_component


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
    """Infer course/lesson labels and build stable output names."""

    LANGUAGE_PATTERN = re.compile(
        r"(?P<separator>[_\-.])(?P<language>es|en|es-es|en-us)(?P<extension>\.[^.]+)$",
        re.IGNORECASE,
    )
    COURSE_PATTERNS = (
        re.compile(
            r"(?:^|[_\- .])(?:curso|course)\s*[_\-.:#]*\s*(\d{1,4})(?!\d)",
            re.IGNORECASE,
        ),
        re.compile(r"\b(\d{1,4})\s*(?:º|°)\s*curso\b", re.IGNORECASE),
    )
    LESSON_PATTERNS = (
        re.compile(
            r"(?:^|[_\- .])(?:cap[ií]tulo|lecci[oó]n|lesson|chapter|clase|tema|unidad)\s*[_\-.:#]*\s*(\d{1,4})\b",
            re.IGNORECASE,
        ),
        re.compile(r"^\s*(\d{1,4})\s*(?:º|°|[._-])\s*", re.IGNORECASE),
    )
    COURSE_TEXT_PATTERNS = (re.compile(r"\b(?:curso|course)\s*[:\-–—.]?\s*([^|/\\]+)", re.IGNORECASE),)
    LESSON_TEXT_PATTERNS = (
        re.compile(
            r"\b(?:lecci[oó]n|lesson|cap[ií]tulo|chapter|clase|tema|unidad)\s*[:\-–—.]?\s*([^|/\\]+)",
            re.IGNORECASE,
        ),
    )
    NOISE_PATTERNS = (
        re.compile(r"^wetransfer[_\-]+", re.IGNORECASE),
        re.compile(r"^drive-download[-_][0-9tz\-]+(?:[-_]\d+[-_]\d+)?[-_]", re.IGNORECASE),
        re.compile(
            r"^(?:zip|rar|7z|archive|compressed|compression|backup|download|descarga)[-_ ]+",
            re.IGNORECASE,
        ),
        re.compile(
            r"^(?:extract(?:ed)?|unzip(?:ped)?|descomprim(?:ido|ida|idos|idas))[-_ ]+",
            re.IGNORECASE,
        ),
        re.compile(r"^files?[-_ ]+(?:from|de)[-_ ]+", re.IGNORECASE),
        re.compile(r"\s*\((?:copy|copia|\d+)\)\s*$", re.IGNORECASE),
        re.compile(r"[_\-]+copy\s*$", re.IGNORECASE),
    )
    GENERIC_TOKENS = {
        "mp4", "wmv", "video", "videos", "audio", "media", "file", "files",
        "archivo", "archivos", "download", "downloads", "descarga", "descargas",
        "compressed", "compression", "archive", "archivo_comprimido", "zip", "rar", "7z",
    }
    FILENAME_ARTIFACT_PATTERN = re.compile(
        r"(?:^|[_\- .])(?:\d{8}t\d{4,6}z(?:[-_]\d+[-_]\d+)?)(?:[_\- .]|$)",
        re.IGNORECASE,
    )

    @classmethod
    def parse(cls, filename: str) -> FileNameInfo:
        path = Path(filename)
        match = cls.LANGUAGE_PATTERN.search(path.name)
        if not match:
            return FileNameInfo(path.name, path.stem, path.suffix.lower())
        return FileNameInfo(path.name, path.stem[: match.start()], path.suffix.lower(), match.group("language").lower())

    @classmethod
    def generate_vtt_name(cls, video_filename: str, target_language: str) -> str:
        info = cls.parse(video_filename)
        return f"{info.stem}_{target_language.lower()}.vtt"

    @staticmethod
    def normalize_video_name(filename: str) -> str:
        return normalize_filename(filename)

    @classmethod
    def resolve_source_metadata(cls, source: Path, extract_root: Path) -> SourceNameMetadata:
        from src.naming_policy import resolve
        return resolve(source, extract_root)

    @classmethod
    def _find_course(cls, values: list[str]) -> int | None:
        for value in values:
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
        return cls._find_label(cls.COURSE_TEXT_PATTERNS, values)

    @classmethod
    def _find_lesson_name(cls, values: list[str]) -> str | None:
        return cls._find_label(cls.LESSON_TEXT_PATTERNS, values)

    @classmethod
    def _find_label(cls, patterns: tuple[re.Pattern[str], ...], values: list[str]) -> str | None:
        for value in values:
            for pattern in patterns:
                match = pattern.search(value)
                if match:
                    label = cls._clean_context(match.group(1))
                    if label:
                        return label
        return None

    @classmethod
    def _infer_context_course_name(cls, values: list[str]) -> str | None:
        for value in values:
            cleaned = cls._clean_context(value)
            if cleaned and not cls._looks_like_download_artifact(value):
                return clean_for_filename(cleaned)
        return None

    @classmethod
    def _infer_context_lesson_name(cls, values: list[str]) -> str | None:
        for value in reversed(values):
            cleaned = cls._clean_context(value)
            if cleaned and not cls._looks_like_download_artifact(value):
                return clean_for_filename(cleaned)
        return None

    @classmethod
    def _build_description(cls, stem: str, *, course: int | None, lesson: int | None, course_name: str | None, lesson_name: str | None) -> str:
        value = stem
        if course is not None:
            value = cls._remove_number(value, course)
        if lesson is not None:
            value = cls._remove_number(value, lesson)
        value = cls._remove_label(value)
        if lesson_name and value.lower() == lesson_name.lower():
            value = ""
        if course_name and value.lower() == course_name.lower():
            value = ""
        return clean_for_filename(value)

    @classmethod
    def _remove_number(cls, value: str, number: int) -> str:
        patterns = (re.compile(rf"(?<!\d){number:02d}(?!\d)"), re.compile(rf"(?<!\d){number}(?!\d)"))
        for pattern in patterns:
            if pattern.search(value):
                return pattern.sub("_", value, count=1)
        return value

    @staticmethod
    def _remove_label(value: str) -> str:
        return re.sub(
            r"(?:^|[_\- .])(?:curso|course|lecci[oó]n|lesson|cap[ií]tulo|chapter|clase|tema|unidad)(?=[_\- .]|$)",
            "_", value, flags=re.IGNORECASE,
        )

    @classmethod
    def _clean_context(cls, value: str) -> str:
        cleaned = Path(value).stem
        cleaned = strip_date_artifacts(cleaned)
        for pattern in cls.NOISE_PATTERNS:
            cleaned = pattern.sub("_", cleaned)
        if cls._looks_like_download_artifact(cleaned):
            cleaned = cls.FILENAME_ARTIFACT_PATTERN.sub("_", cleaned)
        return clean_for_filename(cleaned)

    @classmethod
    def _looks_like_download_artifact(cls, value: str) -> bool:
        return bool(cls.FILENAME_ARTIFACT_PATTERN.search(value))

    @classmethod
    def _remove_generic_tokens(cls, value: str) -> str:
        tokens = [token for token in re.split(r"[_ ]+", value) if token]
        return "_".join(token for token in tokens if token.lower() not in cls.GENERIC_TOKENS)

    @staticmethod
    def _label_or_default(value: str | None, default: str) -> str:
        return value.strip() if value and value.strip() else default


def _sanitize_text(value: str) -> str:
    return clean_for_filename(value)


# Supported timestamp noise:
# YYYYMMDD, YYYYMMDD_HHMMSS, YYYYMMDD_HH_MM, YYYY-MM-DD_HH:MM:SS,
# YYYY/MM/DD, DD/MM/YYYY, MM/DD/YYYY and equivalent -, _, . forms.
# The time portion is optional and may use :, _, -, ., or no separators.
_DATE_ARTIFACT_PATTERN = re.compile(
    r"(?<!\d)(?:"
    r"(?:19|20)\d{2}[-_/.]\d{1,2}[-_/.]\d{1,2}|"
    r"\d{1,2}[-_/.]\d{1,2}[-_/.](?:19|20)\d{2}|"
    r"(?:19|20)\d{6}|"
    r"\d{2}\d{2}\d{4}"
    r")"
    r"(?:[T _-]?(?:[01]?\d|2[0-3])(?:[:_.-]?[0-5]\d)(?:[:_.-]?[0-5]\d)?(?:Z|[+-]\d{2}:?\d{2})?)?"
    r"(?!\d)",
    re.IGNORECASE,
)


def strip_date_artifacts(value: str) -> str:
    """Remove date/time suffix noise without removing ordinary numeric identifiers."""
    return _DATE_ARTIFACT_PATTERN.sub("_", value)


def clean_for_filename(value: str) -> str:
    """Sanitize logical names with a stable cross-platform separator policy."""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", normalized)
    normalized = re.sub(r"[\s\-_.—–−‒―]+", "_", normalized)
    return normalized.strip("_.-")


def normalize_filename(filename: str) -> str:
    path = Path(filename)
    return f"{clean_for_filename(strip_date_artifacts(path.stem))}{path.suffix.lower()}"


def normalize_component(value: str) -> str:
    return _sanitize_text(value)


def normalize_comparison_key(filename: str) -> str:
    """Normalize a media title for duplicate-candidate matching."""
    path = Path(filename)
    value = FileNameFormatter._clean_context(path.stem)
    value = strip_date_artifacts(value)
    value = FileNameFormatter._remove_generic_tokens(value)
    value = re.sub(r"[^a-zA-Z0-9]+", " ", _sanitize_text(value)).lower().strip()
    return re.sub(r"\s+", " ", value)


def normalized_name_similarity(left: str, right: str) -> float:
    """Return a combined character/token similarity score for two normalized names."""
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


def fit_output_stem(stem: str, parent: Path, unique_suffix: str | None = None, reserve_suffixes: tuple[str, ...] = ()) -> str:
    """Fit an output stem to the host filesystem, reserving artifact suffix space."""
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
