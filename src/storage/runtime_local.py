from __future__ import annotations

from pathlib import Path

from src.runtime_paths import runtime_storage_paths
from src.storage.local import LocalStorageProvider


class RuntimeLocalStorageProvider(LocalStorageProvider):
    """Local provider whose internal state never lives beside the installed EXE."""

    def __init__(self, retain_sources: bool = True, input_min_age_seconds: int = 60) -> None:
        super().__init__(retain_sources, input_min_age_seconds)
        self.runtime_paths = runtime_storage_paths()

    def _folder(self, value: str) -> Path:
        normalized = value.removeprefix("local://").replace("\\", "/").strip("/")
        if normalized == "storage" or normalized.startswith("storage/"):
            relative = normalized.removeprefix("storage/")
            return self.runtime_paths["root"] / relative if relative else self.runtime_paths["root"]
        return super()._folder(value)
