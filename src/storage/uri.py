from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import unquote, urlparse


@dataclass(frozen=True)
class StorageUri:
    scheme: str
    value: str


def parse_storage_uri(value: str) -> StorageUri:
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme != "local":
        scheme = parsed.scheme.lower()
        if scheme not in {"gdrive", "rclone"}:
            raise ValueError(f"Unsupported storage URI scheme: {parsed.scheme}")
        raw = parsed.netloc + parsed.path
        return StorageUri(scheme, unquote(raw).lstrip("/"))

    if value.startswith("local://"):
        raw = value[len("local://") :]
        return StorageUri("local", unquote(raw))

    raise ValueError(f"Storage URI must use local://, gdrive:// or rclone:// (received: {value!r})")
