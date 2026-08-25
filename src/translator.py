from __future__ import annotations

import logging
import random
import time
from typing import Any

from config.settings import AppSettings
from src.translation_providers import TranslationProvider, build_translation_provider

logger = logging.getLogger(__name__)


class TextTranslator:
    """Resilient batched translation with sequential provider fallback."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._last_request_at = 0.0
        self._failed_segments = 0
        self._providers: dict[str, TranslationProvider] = {}
        self._failed_provider_errors: dict[str, str] = {}

    @property
    def _provider_names(self) -> list[str]:
        configured = [self.settings.translation_provider, *self.settings.translation_fallback_providers]
        names: list[str] = []
        for name in configured:
            normalized = str(name).strip().lower().replace("-", "_")
            if normalized and normalized not in names:
                names.append(normalized)
        return names

    def _get_provider(self, name: str) -> TranslationProvider:
        if name not in self._providers:
            self._providers[name] = build_translation_provider(name, self.settings)
        return self._providers[name]

    def _wait_for_slot(self) -> None:
        interval = max(0.0, self.settings.translation_min_request_interval_seconds)
        elapsed = time.monotonic() - self._last_request_at
        if interval > elapsed:
            time.sleep(interval - elapsed)

    def _backoff(self, attempt: int) -> None:
        base = max(0.25, self.settings.translation_retry_delay_seconds)
        delay = min(
            self.settings.translation_max_backoff_seconds,
            base * (2 ** max(0, attempt - 1)),
        )
        delay += random.uniform(0.0, min(0.5, delay * 0.1))
        time.sleep(delay)

    def translate_segments(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        translated_by_index: dict[int, str] = {}
        failed_by_index: set[int] = set()
        errors_by_index: dict[int, list[str]] = {}
        providers_by_index: dict[int, str] = {}
        pending = [
            (i, str(segment.get("text", "")).strip())
            for i, segment in enumerate(segments)
            if str(segment.get("text", "")).strip()
        ]
        batch_size = max(1, int(self.settings.translation_batch_size))
        cursor = 0

        while cursor < len(pending):
            batch = pending[cursor : cursor + batch_size]
            indexes = [index for index, _ in batch]
            texts = [text for _, text in batch]
            outputs, failures, provider_names, provider_errors = self._translate_batch_with_fallback(texts, indexes)
            for index, text, output in zip(indexes, texts, outputs, strict=True):
                if output:
                    translated_by_index[index] = output.strip()
                    providers_by_index[index] = provider_names[index]
                else:
                    translated_by_index[index] = text
                    failed_by_index.add(index)
                    errors_by_index[index] = provider_errors.get(index, [])
            cursor += len(batch)
            if failures and len(batch) > 1:
                batch_size = max(1, len(batch) // 2)

        translated = []
        for index, segment in enumerate(segments):
            item = {
                "start": segment["start"],
                "end": segment["end"],
                "text": translated_by_index.get(index, ""),
            }
            if index in providers_by_index:
                item["translation_provider"] = providers_by_index[index]
            if index in failed_by_index:
                item["translation_failed"] = True
                if errors_by_index.get(index):
                    item["translation_errors"] = errors_by_index[index]
            translated.append(item)

        if failed_by_index:
            logger.error(
                "Translation completed with %d/%d segment(s) unresolved; original text retained for failed segments",
                len(failed_by_index),
                len(pending),
            )
        else:
            logger.info("Translation completed successfully: %d segment(s)", len(pending))
        return translated

    def _translate_batch_with_fallback(
        self, texts: list[str], indexes: list[int]
    ) -> tuple[list[str], bool, dict[int, str], dict[int, list[str]]]:
        outputs_by_position: dict[int, str] = {}
        provider_by_index: dict[int, str] = {}
        errors_by_index: dict[int, list[str]] = {index: [] for index in indexes}
        unresolved = list(range(len(texts)))

        for provider_name in self._provider_names:
            if not unresolved:
                break
            try:
                provider = self._get_provider(provider_name)
            except Exception as exc:
                self._failed_provider_errors[provider_name] = str(exc)
                logger.error(
                    "Translation provider '%s' is unavailable; trying next provider: %s",
                    provider_name,
                    exc,
                )
                for position in unresolved:
                    errors_by_index[indexes[position]].append(f"{provider_name}: {type(exc).__name__}: {exc}")
                continue

            active_texts = [texts[position] for position in unresolved]
            active_indexes = [indexes[position] for position in unresolved]
            try:
                outputs = self._translate_batch_with_retries(
                    provider,
                    provider_name,
                    active_texts,
                    active_indexes,
                )
            except Exception as exc:
                logger.error(
                    "Provider '%s' exhausted %d attempt(s) for batch segments %s-%s; original error: %s",
                    provider_name,
                    self.settings.effective_translation_retries,
                    active_indexes[0],
                    active_indexes[-1],
                    exc,
                )
                for index in active_indexes:
                    errors_by_index[index].append(f"{provider_name}: {type(exc).__name__}: {exc}")
                continue

            next_unresolved: list[int] = []
            for position, output in zip(unresolved, outputs, strict=True):
                index = indexes[position]
                if output.strip():
                    outputs_by_position[position] = output.strip()
                    provider_by_index[index] = provider_name
                else:
                    next_unresolved.append(position)
                    errors_by_index[index].append(f"{provider_name}: empty translation result")

            if next_unresolved and provider_name != self._provider_names[-1]:
                logger.warning(
                    "Provider '%s' translated %d/%d segment(s); falling back only for %d unresolved segment(s)",
                    provider_name,
                    len(unresolved) - len(next_unresolved),
                    len(unresolved),
                    len(next_unresolved),
                )
            unresolved = next_unresolved

        final_outputs = [outputs_by_position.get(position, "") for position in range(len(texts))]
        failed = bool(unresolved)
        self._failed_segments += len(unresolved)
        if failed:
            logger.error(
                "All configured translation providers failed for segments %s",
                ", ".join(str(index + 1) for index in (indexes[position] for position in unresolved)),
            )
        return final_outputs, failed, provider_by_index, errors_by_index

    def _translate_batch_with_retries(
        self,
        provider: TranslationProvider,
        provider_name: str,
        texts: list[str],
        indexes: list[int],
    ) -> list[str]:
        last_error: Exception | None = None
        for attempt in range(1, self.settings.effective_translation_retries + 1):
            try:
                self._wait_for_slot()
                self._last_request_at = time.monotonic()
                outputs = provider.translate_batch(texts)
                if not isinstance(outputs, list) or len(outputs) != len(texts):
                    output_count = len(outputs) if isinstance(outputs, list) else "invalid"
                    raise RuntimeError(
                        f"Translator returned {output_count} items for {len(texts)} inputs"
                    )
                return [str(item or "") for item in outputs]
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Batch translation failed with provider '%s' for segments %s-%s (attempt %d/%d): %s",
                    provider_name,
                    indexes[0],
                    indexes[-1],
                    attempt,
                    self.settings.effective_translation_retries,
                    exc,
                )
                if attempt < self.settings.effective_translation_retries:
                    self._backoff(attempt)
        assert last_error is not None
        raise last_error
