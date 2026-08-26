from __future__

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


def _sanitize_text(value: str) -> str:
    return clean_for_filename(value)


def clean_for_filename(value: str) -> str:
    """Sanitize logical names with a stable cross-platform separator policy."""
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", normalized)
    normalized = re.sub(r"[\s\-_.—–−‒―]+", "_", normalized)
    return normalized.strip("_.-")


def normalize_filename(filename: str) -> str:
    path = Path(filename)
    return f"{clean_for_filename(path.stem)}{path.suffix.lower()}"


def normalize_component(value: str) -> str:
    return _sanitize_text(value)


def normalize_comparison_key(filename: str) -> str:
    path = Path(filename)
    value = clean_for_filename(path.stem)
    value = re.sub(r"(?:[_\- .]+)(?:20\d{2}[-_](?:0?[1-9]|1[0-2])[-_](?:0?[1-9]|[12]\d|3[01])[_-]\d{4,6})(?:[-_]\d+)?$", "", value, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9]+", " ", value)).lower().strip()


def normalized_name_similarity(left: str, right: str) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    left_tokens, right_tokens = set(left.split()), set(right.split())
    sequence_score = SequenceMatcher(None, left, right).ratio()
    union = left_tokens | right_tokens
    token_score = len(left_tokens & right_tokens) / len(union) if union else 0.0
    return 0.65 * sequence_score + 0.35 * token_score


def fit_output_stem(stem: str, parent: Path, unique_suffix: str | None = None, reserve_suffixes: tuple[str, ...] = ()) -> str:
    suffix = f"__{unique_suffix}" if unique_suffix else ""
    candidate = fit_component(stem, parent, suffix=suffix)
    if not reserve_suffixes:
        return candidate
    from src.path_limits import get_filesystem_limits
    limits = get_filesystem_limits(parent)
    allowed = max(1, limits.max_component - max((len(item.encode("utf-8")) for item in reserve_suffixes), default=0))
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
