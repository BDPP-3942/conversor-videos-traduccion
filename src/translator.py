from __future__ import annotations

import logging
import secrets
import time
from typing import Any

from config.settings import AppSettings, local_storage_paths
from src.translation_providers import (
    TranslationProvider,
    TranslationQuotaError,
    build_translation_provider,
)
from src.translation_quota import TranslationQuotaExceeded, TranslationQuotaGuard

logger = logging.getLogger(__name__)
BATCH_MAX_ATTEMPTS = 2


class TextTranslator:
    """Batched translation with bounded retries and sequential provider fallback."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._last_request_at = 0.0
        self._providers: dict[str, TranslationProvider] = {}
        self._failed_segments = 0
        self._quota = TranslationQuotaGuard(local_storage_paths()["state"] / "translation_quotas.json")

    @property
    def _provider_names(self) -> list[str]:
        configured = [self.settings.translation_provider, *self.settings.translation_fallback_providers]
        result: list[str] = []
        for name in configured:
            normalized = str(name).strip().lower().replace("-", "_")
            if normalized and normalized not in result:
                result.append(normalized)
        return result

    def _get_provider(self, name: str) -> TranslationProvider:
        if name not in self._providers:
            self._providers[name] = build_translation_provider(name, self.settings)
        return self._providers[name]

    def _wait(self) -> None:
        interval = max(0.0, self.settings.translation_min_request_interval_seconds)
        remaining = interval - (time.monotonic() - self._last_request_at)
        if remaining > 0:
            time.sleep(remaining)

    def _backoff(self, attempt: int) -> None:
        base = max(0.25, self.settings.translation_retry_delay_seconds)
        delay = min(self.settings.translation_max_backoff_seconds, base * 2 ** (attempt - 1))
        jitter = secrets.SystemRandom().uniform(0, min(0.5, delay * 0.1))
        time.sleep(delay + jitter)

    def translate_segments(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        translated: dict[int, str] = {}
        failed: set[int] = set()
        errors: dict[int, list[str]] = {}
        providers: dict[int, str] = {}
        pending = [(i, str(item.get("text", "")).strip()) for i, item in enumerate(segments) if str(item.get("text", "")).strip()]
        size = max(1, int(self.settings.translation_batch_size))
        for offset in range(0, len(pending), size):
            batch = pending[offset : offset + size]
            indexes = [item[0] for item in batch]
            texts = [item[1] for item in batch]
            outputs, provider_map, batch_errors = self._translate_batch(texts, indexes)
            for index, text, output in zip(indexes, texts, outputs, strict=True):
                if output:
                    translated[index] = output
                    if index in provider_map:
                        providers[index] = provider_map[index]
                else:
                    translated[index] = text
                    failed.add(index)
                    errors[index] = batch_errors.get(index, [])

        result = []
        for index, segment in enumerate(segments):
            item = {"start": segment["start"], "end": segment["end"], "text": translated.get(index, "")}
            if index in providers:
                item["translation_provider"] = providers[index]
            if index in failed:
                item["translation_failed"] = True
                item["translation_errors"] = errors[index]
            result.append(item)
        if failed:
            logger.error("Translation completed partially: %d/%d segment(s) unresolved", len(failed), len(pending))
        return result

    def _translate_batch(self, texts: list[str], indexes: list[int]) -> tuple[list[str], dict[int, str], dict[int, list[str]]]:
        unresolved = list(range(len(texts)))
        outputs: dict[int, str] = {}
        provider_map: dict[int, str] = {}
        errors = {index: [] for index in indexes}
        names = self._provider_names
        previous: str | None = None

        for position, name in enumerate(names):
            if not unresolved:
                break
            active_texts = [texts[i] for i in unresolved]
            active_indexes = [indexes[i] for i in unresolved]
            if previous:
                logger.info("Switching translation provider from '%s' to '%s' for %d unresolved segment(s)", previous, name, len(active_indexes))
            else:
                logger.info("Starting translation provider '%s' for %d segment(s)", name, len(active_indexes))
            previous = name
            try:
                provider = self._get_provider(name)
                self._quota.reserve(name, active_texts)
                batch_outputs = self._retry_batch(provider, name, active_texts, active_indexes)
            except TranslationQuotaExceeded as exc:
                logger.warning("Provider '%s' local quota exhausted (%d/%d); switching provider", name, exc.used, exc.limit)
                for index in active_indexes:
                    errors[index].append(str(exc))
                continue
            except TranslationQuotaError as exc:
                self._quota.record_quota_failure(name)
                logger.warning("Provider '%s' reported quota exhaustion; switching provider: %s", name, exc)
                for index in active_indexes:
                    errors[index].append(f"{name}: {exc}")
                continue
            except Exception as exc:
                logger.error("Provider '%s' failed after %d batch attempt(s): %s", name, BATCH_MAX_ATTEMPTS, exc)
                for index in active_indexes:
                    errors[index].append(f"{name}: {type(exc).__name__}: {exc}")
                continue

            next_unresolved: list[int] = []
            for local, output in zip(unresolved, batch_outputs, strict=True):
                index = indexes[local]
                if str(output).strip():
                    outputs[local] = str(output).strip()
                    provider_map[index] = name
                else:
                    next_unresolved.append(local)
                    errors[index].append(f"{name}: empty translation result")
            unresolved = next_unresolved

        self._failed_segments += len(unresolved)
        return [outputs.get(i, "") for i in range(len(texts))], provider_map, errors

    def _retry_batch(self, provider: TranslationProvider, name: str, texts: list[str], indexes: list[int]) -> list[str]:
        last_error: Exception | None = None
        for attempt in range(1, BATCH_MAX_ATTEMPTS + 1):
            logger.info("Provider '%s' batch attempt %d/%d for segments %s-%s", name, attempt, BATCH_MAX_ATTEMPTS, indexes[0], indexes[-1])
            try:
                self._wait()
                self._last_request_at = time.monotonic()
                result = provider.translate_batch(texts)
                if not isinstance(result, list) or len(result) != len(texts):
                    count = len(result) if isinstance(result, list) else "invalid"
                    raise RuntimeError(f"Translator returned {count} items for {len(texts)} inputs")
                logger.info("Translation batch succeeded with provider '%s' on attempt %d/%d", name, attempt, BATCH_MAX_ATTEMPTS)
                return [str(item or "") for item in result]
            except Exception as exc:
                last_error = exc
                logger.warning("Batch translation failed with provider '%s' on attempt %d/%d: %s", name, attempt, BATCH_MAX_ATTEMPTS, exc)
                if attempt < BATCH_MAX_ATTEMPTS:
                    self._backoff(attempt)
        if last_error is None:
            raise RuntimeError("Translation batch failed without an exception")
        raise last_error
