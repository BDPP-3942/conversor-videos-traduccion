from __future__ import annotations

import json
import threading
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path


class TranslationQuotaExceeded(RuntimeError):
    """Raised before a provider call when its configured free quota is exhausted."""

    def __init__(self, provider: str, used: int, limit: int, window: str, unit: str) -> None:
        self.provider = provider
        self.used = used
        self.limit = limit
        self.window = window
        self.unit = unit
        super().__init__(f"{provider} free quota exhausted: {used}/{limit} {unit} in {window} window")


class TranslationQuotaGuard:
    """Persist conservative free-tier usage reservations across concurrent requests."""

    DEEPL_LIMIT = 500_000
    MYMEMORY_ANONYMOUS_REQUESTS = 100
    MYMEMORY_REGISTERED_REQUESTS = 1_000

    def __init__(self, state_path: Path, mymemory_registered: bool = False) -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.mymemory_registered = mymemory_registered
        self._lock = threading.Lock()

    def _quota(self, provider: str, now: datetime) -> tuple[str, int, str] | None:
        if provider == "deepl":
            return now.strftime("%Y-%m"), self.DEEPL_LIMIT, "characters"
        if provider in {"mymemory", "my_memory"}:
            limit = self.MYMEMORY_REGISTERED_REQUESTS if self.mymemory_registered else self.MYMEMORY_ANONYMOUS_REQUESTS
            return now.strftime("%Y-%m-%d"), limit, "requests"
        return None

    def _read(self) -> dict:
        if not self.state_path.is_file():
            return {}
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _write(self, data: dict) -> None:
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.state_path)

    def reserve(self, provider: str, texts: Iterable[str]) -> int:
        provider = provider.lower().replace("-", "_")
        values = [str(text) for text in texts]
        if not values:
            return 0
        now = datetime.now(UTC)
        quota = self._quota(provider, now)
        if quota is None:
            return sum(len(text) for text in values)
        window, limit, unit = quota
        count = len(values) if unit == "requests" else sum(len(text) for text in values)
        with self._lock:
            data = self._read()
            entry = data.get(provider, {})
            used = int(entry.get("used", 0)) if entry.get("window") == window else 0
            if used + count > limit:
                raise TranslationQuotaExceeded(provider, used, limit, window, unit)
            data[provider] = {"window": window, "used": used + count}
            self._write(data)
        return count

    def record_quota_failure(self, provider: str) -> None:
        provider = provider.lower().replace("-", "_")
        now = datetime.now(UTC)
        quota = self._quota(provider, now)
        if quota is None:
            return
        window, limit, _ = quota
        with self._lock:
            data = self._read()
            data[provider] = {"window": window, "used": limit}
            self._write(data)

    def usage(self, provider: str) -> dict[str, int | str] | None:
        provider = provider.lower().replace("-", "_")
        quota = self._quota(provider, datetime.now(UTC))
        if quota is None:
            return None
        window, limit, unit = quota
        with self._lock:
            entry = self._read().get(provider, {})
        used = int(entry.get("used", 0)) if entry.get("window") == window else 0
        return {"window": window, "used": used, "limit": limit, "unit": unit}
