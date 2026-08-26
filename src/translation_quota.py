from __future__ import annotations

import json
import threading
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path


class TranslationQuotaExceeded(RuntimeError):
    """Raised before a provider call when its configured free quota is exhausted."""

    def __init__(self, provider: str, used: int, limit: int, window: str, unit: str = "characters") -> None:
        self.provider = provider
        self.used = used
        self.limit = limit
        self.window = window
        self.unit = unit
        super().__init__(f"{provider} free quota exhausted: {used}/{limit} {unit} in {window} window")


class TranslationQuotaGuard:
    """Persist local free-tier usage reservations across concurrent requests."""

    LIMITS = {
        "deepl": ("%Y-%m", 500_000, "characters"),
        "mymemory": ("%Y-%m-%d", 50_000, "characters"),
    }

    def __init__(self, state_path: Path) -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

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
        count = sum(len(str(text)) for text in texts)
        if count <= 0 or provider not in self.LIMITS:
            return count

        now = datetime.now(UTC)
        window_format, limit, unit = self.LIMITS[provider]
        window = now.strftime(window_format)
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
        if provider not in self.LIMITS:
            return
        now = datetime.now(UTC)
        window_format, limit, _ = self.LIMITS[provider]
        window = now.strftime(window_format)
        with self._lock:
            data = self._read()
            data[provider] = {"window": window, "used": limit}
            self._write(data)

    def usage(self, provider: str) -> dict[str, int | str] | None:
        provider = provider.lower().replace("-", "_")
        if provider not in self.LIMITS:
            return None
        window_format, limit, unit = self.LIMITS[provider]
        window = datetime.now(UTC).strftime(window_format)
        with self._lock:
            entry = self._read().get(provider, {})
        used = int(entry.get("used", 0)) if entry.get("window") == window else 0
        return {"window": window, "used": used, "limit": limit, "unit": unit}
