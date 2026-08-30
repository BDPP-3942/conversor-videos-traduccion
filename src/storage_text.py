from __future__ import annotations

from pathlib import Path

from src.storage.base import StorageFile, StorageProvider
from src.storage.uri import parse_storage_uri


def load_storage_text_file(storage: StorageProvider, uri: str, *, label: str) -> str:
    """Download one UTF-8 text file addressed by a storage URI."""
    parsed = parse_storage_uri(uri)
    value = parsed.value.rstrip("/")
    if not value:
        raise ValueError(f"{label} path is empty")
    parent_value, separator, name = value.rpartition("/")
    if not separator or not parent_value or not name:
        raise ValueError(f"{label} must identify a file below a storage folder: {uri}")
    candidates = [
        item
        for item in storage.list_children(parent_value)
        if not item.is_directory and item.name == name
    ]
    if not candidates:
        raise FileNotFoundError(f"{label} does not exist in storage: {uri}")
    if len(candidates) > 1:
        raise RuntimeError(f"{label} is ambiguous in storage: {uri}")

    temporary = Path.cwd() / ".prompt-read.tmp"
    try:
        storage.download_file(candidates[0], temporary)
        try:
            text = temporary.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{label} is not valid UTF-8: {uri}") from exc
    finally:
        temporary.unlink(missing_ok=True)
    text = text.strip()
    if not text:
        raise ValueError(f"{label} is empty: {uri}")
    return text
