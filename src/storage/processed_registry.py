from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ProcessedRegistry:
    """Append-only registry of successfully processed source archives."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        entries: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                entries.append(value)
        return entries

    def contains_success(self, source_name: str, sha256: str) -> bool:
        return any(
            item.get("source_name") == source_name and item.get("sha256") == sha256 and item.get("status") == "success"
            for item in self.entries()
        )

    def append_success(
        self,
        *,
        source_name: str,
        sha256: str,
        size: int,
        archive_name: str,
        output_folders: list[str],
    ) -> None:
        payload = {
            "source_name": source_name,
            "sha256": sha256,
            "size": size,
            "archive_name": archive_name,
            "output_folders": output_folders,
            "processed_at": datetime.now(UTC).isoformat(),
            "status": "success",
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
