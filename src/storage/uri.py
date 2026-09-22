from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse


@dataclass(frozen=True)
class StorageUri:
    scheme: str
    value: str


def parse_storage_uri(value: str) -> StorageUri:
    raw_value = str(value).strip()
    if not raw_value:
        raise ValueError("Storage URI cannot be empty")
    if raw_value.startswith("local://"):
        return StorageUri("local", unquote(raw_value[len("local://") :]))

    parsed = urlparse(raw_value)
    is_windows_path = len(parsed.scheme) == 1 and len(raw_value) > 2 and raw_value[1] == ":"
    if parsed.scheme and not is_windows_path:
        scheme = parsed.scheme.lower()
        if scheme in {"http", "https"}:
            return StorageUri(scheme, raw_value)
        if scheme not in {"gdrive", "rclone"}:
            raise ValueError(f"Unsupported storage URI scheme: {parsed.scheme}")
        raw = parsed.netloc + parsed.path
        return StorageUri(scheme, unquote(raw).lstrip("/"))
    return StorageUri("local", str(Path(raw_value).expanduser()))
