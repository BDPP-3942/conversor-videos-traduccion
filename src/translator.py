from __future__ import annotations

import logging
import time
from typing import Any

from config.settings import AppSettings

logger = logging.getLogger(__name__)


class TextTranslator:
    """Batch-oriented translator with fallback to individual requests."""

    def __init__(self, settings: AppSettings) -> None:
        try:
            from deep_translator import GoogleTranslator
        except ImportError as exc:
            raise RuntimeError("Translation support requires the deep-translator package") from exc
        self.settings = settings
        self.translator = GoogleTranslator(source=settings.source_lang, target=settings.target_lang)

    def translate_segments(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        translated_by_index: dict[int, str] = {}
        pending: list[tuple[int, str]] = [
            (i, str(segment.get("text", "")).strip())
            for i, segment in enumerate(segments)
            if str(segment.get("text", "")).strip()
        ]
        batch_size = max(1, int(self.settings.translation_batch_size))

        for start in range(0, len(pending), batch_size):
            batch = pending[start : start + batch_size]
            indexes = [index for index, _ in batch]
            texts = [text for _, text in batch]
            outputs = self._translate_batch_with_retries(texts, indexes)
            for index, output in zip(indexes, outputs):
                translated_by_index[index] = output.strip() if output else ""

        translated = []
        for index, segment in enumerate(segments):
            translated.append(
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": translated_by_index.get(index, ""),
                }
            )
        return translated

    def _translate_batch_with_retries(self, texts: list[str], indexes: list[int]) -> list[str]:
        last_error: Exception | None = None
        for attempt in range(1, self.settings.translation_retries + 1):
            try:
                outputs = self.translator.translate_batch(texts)
                if not isinstance(outputs, list) or len(outputs) != len(texts):
                    raise RuntimeError(
                        f"Translator returned {len(outputs) if isinstance(outputs, list) else 'invalid'} "
                        f"items for {len(texts)} inputs"
                    )
                return [str(item or "") for item in outputs]
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Batch translation failed for segments %s-%s (attempt %d/%d): %s",
                    indexes[0], indexes[-1], attempt, self.settings.translation_retries, exc,
                )
                if attempt < self.settings.translation_retries:
                    time.sleep(self.settings.translation_retry_delay_seconds)

        logger.warning("Falling back to individual translation for batch %s-%s", indexes[0], indexes[-1])
        outputs: list[str] = []
        for index, text in zip(indexes, texts):
            outputs.append(self._translate_one_with_retries(text, index, last_error))
        return outputs

    def _translate_one_with_retries(
        self, text: str, index: int, previous_error: Exception | None = None
    ) -> str:
        last_error = previous_error
        for attempt in range(1, self.settings.translation_retries + 1):
            try:
                return (self.translator.translate(text) or "").strip()
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Translation failed for segment %d (attempt %d/%d): %s",
                    index + 1, attempt, self.settings.translation_retries, exc,
                )
                if attempt < self.settings.translation_retries:
                    time.sleep(self.settings.translation_retry_delay_seconds)
        raise RuntimeError(f"Translation failed for segment {index + 1}") from last_error
