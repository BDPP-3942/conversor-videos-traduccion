from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MANIFEST_VERSION = 2


def write_manifest(
    path: Path,
    entries: list[dict[str, Any]],
    *,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Write a resumable manifest while remaining UTF-8 compatible."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": MANIFEST_VERSION,
        "metadata": metadata or {},
        "entries": entries,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_manifest(path: Path) -> dict[str, Any]:
    """Read v2 manifests and transparently load legacy list-style manifests."""
    if not path.is_file():
        return {"version": 0, "metadata": {}, "entries": []}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"version": 0, "metadata": {}, "entries": []}

    if isinstance(payload, list):
        return {"version": 1, "metadata": {}, "entries": payload}
    if not isinstance(payload, dict):
        return {"version": 0, "metadata": {}, "entries": []}

    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    return {
        "version": int(payload.get("version", 1) or 1),
        "metadata": metadata,
        "entries": entries,
    }
