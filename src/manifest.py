from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

MANIFEST_VERSION = 2


def write_manifest(path: Path, entries: list[dict[str, Any]], *, metadata: dict[str, Any] | None = None) -> None:
    """Publish a complete manifest atomically so a crash cannot expose partial JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": MANIFEST_VERSION, "metadata": metadata or {}, "entries": entries}
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with temporary.open("r+b") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def read_manifest(path: Path) -> dict[str, Any]:
    """Read manifests; malformed existing state is an error, not an empty manifest."""
    if not path.is_file():
        return {"version": 0, "metadata": {}, "entries": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Manifest exists but is unreadable or corrupt: {path}") from exc
    if isinstance(payload, list):
        return {"version": 1, "metadata": {}, "entries": payload}
    if not isinstance(payload, dict):
        raise RuntimeError(f"Manifest has invalid top-level structure: {path}")
    entries = payload.get("entries", [])
    metadata = payload.get("metadata", {})
    if not isinstance(entries, list) or not isinstance(metadata, dict):
        raise RuntimeError(f"Manifest has invalid entries/metadata structure: {path}")
    return {"version": int(payload.get("version", 1) or 1), "metadata": metadata, "entries": entries}
