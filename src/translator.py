from __future__ import annotations

import logging
import random
import time
from typing import Any

from config.settings import AppSettings

logger = logging.getLogger(__name__)


class TextTranslator:
    """Resilient Google translation with adaptive batches and rate limiting."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self._last_request_at = 0.0
        self._failed_segments = 0
        self._translator_factory = self._load_translator_factory()
        self.translator = self._new_translator()

    def _load_translator_factory(self):
        try:
            from deep_translator import GoogleTranslator
        except ImportError as exc:
            raise RuntimeError("Translation support requires the deep-translator package") from exc
        return GoogleTranslator

    def _new_translator(self):
        return self._translator_factory(
            source=self.settings.source_lang,
            target=self.settings.target_lang,
        )

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
            outputs, failures = self._translate_batch_adaptive(texts, indexes)
            for index, text, output in zip(indexes, texts, outputs, strict=True):
                if output:
                    translated_by_index[index] = output.strip()
                else:
                    translated_by_index[index] = text
                    failed_by_index.add(index)
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
            if index in failed_by_index:
                item["translation_failed"] = True
            translated.append(item)

        if failed_by_index:
            logger.error(
                "Translation completed with %d/%d segment(s) unresolved; original text retained for failed segments",
                len(failed_by_index), len(pending),
            )
        else:
            logger.info("Translation completed successfully: %d segment(s)", len(pending))
        return translated

    def _translate_batch_adaptive(
        self, texts: list[str], indexes: list[int]
    ) -> tuple[list[str], bool]:
        last_error: Exception | None = None
        for attempt in range(1, self.settings.translation_retries + 1):
            try:
                self._wait_for_slot()
                self._last_request_at = time.monotonic()
                outputs = self.translator.translate_batch(texts)
                if not isinstance(outputs, list) or len(outputs) != len(texts):
                    output_count = len(outputs) if isinstance(outputs, list) else "invalid"
                    raise RuntimeError(
                        f"Translator returned {output_count} items for {len(texts)} inputs"
                    )
                return [str(item or "") for item in outputs], False
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Batch translation failed for segments %s-%s (attempt %d/%d): %s",
                    indexes[0],
                    indexes[-1],
                    attempt,
                    self.settings.translation_retries,
                    exc,
                )
                try:
                    self.translator = self._new_translator()
                except Exception:
                    logger.exception("Could not recreate translation client")
                if attempt < self.settings.translation_retries:
                    self._backoff(attempt)

        logger.warning(
            "Falling back to individual translation for batch %s-%s after %d attempts",
            indexes[0],
            indexes[-1],
            self.settings.translation_retries,
        )
        outputs: list[str] = []
        had_failure = False
        for index, text in zip(indexes, texts, strict=True):
            output = self._translate_one_with_retries(text, index, last_error)
            if not output:
                had_failure = True
            outputs.append(output)
        return outputs, had_failure

    def _translate_one_with_retries(
        self,
        text: str,
        index: int,
        previous_error: Exception | None = None,
    ) -> str:
        last_error = previous_error
        for attempt in range(1, self.settings.translation_retries + 1):
            try:
                self._wait_for_slot()
                self._last_request_at = time.monotonic()
                result = (self.translator.translate(text) or "").strip()
                if not result:
                    raise RuntimeError("Translator returned an empty result")
                return result
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Translation failed for segment %d (attempt %d/%d): %s",
                    index + 1,
                    attempt,
                    self.settings.translation_retries,
                    exc,
                )
                try:
                    self.translator = self._new_translator()
                except Exception:
                    logger.exception("Could not recreate translation client")
                if attempt < self.settings.translation_retries:
                    self._backoff(attempt)

        logger.error(
            "Translation permanently failed for segment %d; preserving source text. Last error: %s",
            index + 1,
            last_error,
        )
        self._failed_segments += 1
        return ""
