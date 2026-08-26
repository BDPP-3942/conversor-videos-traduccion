from __future__ import annotations

import logging
import os
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from config.settings import AppSettings, local_storage_paths
from src.translation_providers import (
    TranslationProvider,
    TranslationQuotaError,
    TranslationRateLimitError,
    build_translation_provider,
)
from src.translation_quota import TranslationQuotaExceeded, TranslationQuotaGuard

logger = logging.getLogger(__name__)
BATCH_MAX_ATTEMPTS = 3
DEFAULT_BATCH_SIZE = 25
PROVIDER_BATCH_SIZES = {"mistral": 25, "deepl": 25, "mymemory": 1}
DEFAULT_PROVIDER_CONCURRENCY = {"mistral": 2, "deepl": 2, "mymemory": 1}


class TextTranslator:
    """Batched cloud translation with quotas, rate limits and bounded concurrency."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._providers: dict[str, TranslationProvider] = {}
        self._failed_segments = 0
        self._quota = TranslationQuotaGuard(
            local_storage_paths()["state"] / "translation_quotas.json",
            mymemory_registered=bool(os.getenv("MYMEMORY_EMAIL", "").strip()),
        )
        self._request_lock = threading.Lock()
        self._last_request_at: dict[str, float] = {}
        self._provider_limits: dict[str, threading.BoundedSemaphore] = {}
        configured_parallel = max(1, int(settings.translation_max_parallel_requests))
        self._global_limit = threading.BoundedSemaphore(configured_parallel)

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

    def _provider_concurrency(self, name: str) -> int:
        configured = int(self.settings.translation_provider_max_parallel_requests)
        if configured > 0:
            return configured
        return DEFAULT_PROVIDER_CONCURRENCY.get(name, 1)

    def _provider_semaphore(self, name: str) -> threading.BoundedSemaphore:
        if name not in self._provider_limits:
            self._provider_limits[name] = threading.BoundedSemaphore(self._provider_concurrency(name))
        return self._provider_limits[name]

    def _wait_for_rate_limit(self, name: str) -> None:
        interval = max(0.0, self.settings.translation_min_request_interval_seconds)
        with self._request_lock:
            now = time.monotonic()
            remaining = interval - (now - self._last_request_at.get(name, 0.0))
            if remaining > 0:
                time.sleep(remaining)
            self._last_request_at[name] = time.monotonic()

    def _backoff(self, attempt: int) -> None:
        base = max(0.25, self.settings.translation_retry_delay_seconds)
        delay = min(self.settings.translation_max_backoff_seconds, base * 2 ** (attempt - 1))
        jitter = secrets.SystemRandom().uniform(0, min(0.5, delay * 0.1))
        time.sleep(delay + jitter)

    def _batch_size(self, name: str) -> int:
        configured = int(self.settings.translation_batch_size)
        if configured > 0:
            return min(configured, PROVIDER_BATCH_SIZES.get(name, DEFAULT_BATCH_SIZE))
        return PROVIDER_BATCH_SIZES.get(name, DEFAULT_BATCH_SIZE)

    def translate_segments(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        translated: dict[int, str] = {}
        failed: set[int] = set()
        errors: dict[int, list[str]] = {}
        providers: dict[int, str] = {}
        pending = [
            (index, str(item.get("text", "")).strip())
            for index, item in enumerate(segments)
            if str(item.get("text", "")).strip()
        ]
        for offset in range(0, len(pending), DEFAULT_BATCH_SIZE):
            batch = pending[offset : offset + DEFAULT_BATCH_SIZE]
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

    def _translate_batch(
        self,
        texts: list[str],
        indexes: list[int],
    ) -> tuple[list[str], dict[int, str], dict[int, list[str]]]:
        unresolved = list(range(len(texts)))
        outputs: dict[int, str] = {}
        provider_map: dict[int, str] = {}
        errors = {index: [] for index in indexes}
        names = self._provider_names

        for name in names:
            if not unresolved:
                break
            active = list(unresolved)
            logger.info("Starting translation provider '%s' for %d unresolved segment(s)", name, len(active))
            results = self._translate_provider_batches(name, texts, indexes, active)
            next_unresolved: list[int] = []
            for local, output, error in results:
                index = indexes[local]
                if output.strip():
                    outputs[local] = output.strip()
                    provider_map[index] = name
                else:
                    next_unresolved.append(local)
                    if error:
                        errors[index].append(error)
            unresolved = next_unresolved

        self._failed_segments += len(unresolved)
        return [outputs.get(index, "") for index in range(len(texts))], provider_map, errors

    def _translate_provider_batches(
        self,
        name: str,
        texts: list[str],
        indexes: list[int],
        active: list[int],
    ) -> list[tuple[int, str, str]]:
        size = self._batch_size(name)
        chunks = [active[offset : offset + size] for offset in range(0, len(active), size)]
        results: list[tuple[int, str, str]] = []
        with ThreadPoolExecutor(max_workers=self._provider_concurrency(name)) as executor:
            futures = {
                executor.submit(self._translate_provider_chunk, name, texts, indexes, chunk): chunk
                for chunk in chunks
            }
            for future in as_completed(futures):
                results.extend(future.result())
        return results

    def _translate_provider_chunk(
        self,
        name: str,
        texts: list[str],
        indexes: list[int],
        chunk: list[int],
    ) -> list[tuple[int, str, str]]:
        active_texts = [texts[index] for index in chunk]
        active_indexes = [indexes[index] for index in chunk]
        try:
            provider = self._get_provider(name)
            self._quota.reserve(name, active_texts)
            outputs = self._retry_batch(provider, name, active_texts, active_indexes)
            return [
                (local, str(output or ""), "" if str(output or "").strip() else f"{name}: empty translation result")
                for local, output in zip(chunk, outputs, strict=True)
            ]
        except TranslationQuotaExceeded as exc:
            message = str(exc)
            logger.warning("Provider '%s' local free quota exhausted; switching provider", name)
            return [(local, "", message) for local in chunk]
        except TranslationQuotaError as exc:
            self._quota.record_quota_failure(name)
            message = f"{name}: {exc}"
            logger.warning("Provider '%s' reported quota exhaustion; switching provider", name)
            return [(local, "", message) for local in chunk]
        except TranslationRateLimitError as exc:
            message = f"{name}: {exc}"
            logger.warning("Provider '%s' rate limited; retrying/falling back", name)
            return [(local, "", message) for local in chunk]
        except Exception as exc:
            message = f"{name}: {type(exc).__name__}: {exc}"
            logger.error("Provider '%s' failed for batch: %s", name, exc)
            return [(local, "", message) for local in chunk]

    def _retry_batch(
        self,
        provider: TranslationProvider,
        name: str,
        texts: list[str],
        indexes: list[int],
    ) -> list[str]:
        last_error: Exception | None = None
        provider_limit = self._provider_semaphore(name)
        with self._global_limit, provider_limit:
            for attempt in range(1, BATCH_MAX_ATTEMPTS + 1):
                logger.info("Provider '%s' batch attempt %d/%d for segments %s-%s", name, attempt, BATCH_MAX_ATTEMPTS, indexes[0], indexes[-1])
                try:
                    self._wait_for_rate_limit(name)
                    result = provider.translate_batch(texts)
                    if not isinstance(result, list) or len(result) != len(texts):
                        count = len(result) if isinstance(result, list) else "invalid"
                        raise RuntimeError(f"Translator returned {count} items for {len(texts)} inputs")
                    return [str(item or "") for item in result]
                except TranslationQuotaError:
                    raise
                except TranslationRateLimitError as exc:
                    last_error = exc
                except Exception as exc:
                    last_error = exc
                if attempt < BATCH_MAX_ATTEMPTS:
                    self._backoff(attempt)
        if last_error is None:
            raise RuntimeError("Translation batch failed without an exception")
        raise last_error
