from __future__ import annotations

import json
import threading
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path


class TranslationQuotaExceeded(RuntimeError):
    """Raised before a provider call when its configured free quota is exhausted."""

    def __init__(self, provider: str, used: int, limit: int, window: str) -> None:
        self.provider = provider
        self.used = used
        self.limit = limit
        self.window = window
        super().__init__(f"{provider} free quota exhausted: {used}/{limit} characters in {window} window")


class TranslationQuotaGuard:
    """Persist local usage counters so free-provider quotas are not exceeded accidentally."""

    def __init__(self, state_path: Path) -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @staticmethod
    def _window(provider: str, now: datetime) -> tuple[str, int]:
        if provider == "deepl":
            return now.strftime("%Y-%m"), 500_000
        if provider == "microsoft":
            return now.strftime("%Y-%m-%dT%H"), 2_000_000
        if provider in {"mymemory", "my_memory"}:
            return now.strftime("%Y-%m-%d"), 50_000
        return "unlimited", 0

    def _read(self) -> dict:
        if not self.state_path.is_file():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _write(self, data: dict) -> None:
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.state_path)

    def reserve(self, provider: str, texts: Iterable[str]) -> int:
        provider = provider.lower().replace("-", "_")
        count = sum(len(str(text)) for text in texts)
        if count <= 0:
            return 0
        if provider not in {"deepl", "microsoft", "mymemory", "my_memory"}:
            return count

        now = datetime.now(UTC)
        window, limit = self._window(provider, now)
        with self._lock:
            data = self._read()
            entry = data.get(provider, {})
            used = int(entry.get("used", 0)) if entry.get("window") == window else 0
            if used + count > limit:
                raise TranslationQuotaExceeded(provider, used, limit, window)
            data[provider] = {"window": window, "used": used + count}
            self._write(data)
        return count

    def record_quota_failure(self, provider: str) -> None:
        """Mark a provider exhausted for its current window after a remote quota error."""
        provider = provider.lower().replace("-", "_")
        now = datetime.now(UTC)
        window, limit = self._window(provider, now)
        if not limit:
            return
        with self._lock:
            data = self._read()
            data[provider] = {"window": window, "used": limit}
            self._write(data)
