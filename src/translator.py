from __future__ import annotations

import logging
import time
from typing import Any

from config.settings import AppSettings

logger = logging.getLogger(__name__)


class TextTranslator:
    def __init__(self, settings: AppSettings) -> None:
        try:
            from deep_translator import GoogleTranslator
        except ImportError as exc:
            raise RuntimeError("Translation support requires the deep-translator package") from exc
        self.settings = settings
        self.translator = GoogleTranslator(
            source=settings.source_lang,
            target=settings.target_lang,
        )

    def translate_segments(self, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        translated = []
        for index, segment in enumerate(segments, start=1):
            text = str(segment.get("text", "")).strip()
            output = self._translate_with_retries(text, index) if text else ""
            translated.append({"start": segment["start"], "end": segment["end"], "text": output})
        return translated

    def _translate_with_retries(self, text: str, index: int) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.settings.translation_retries + 1):
            try:
                return (self.translator.translate(text) or "").strip()
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Translation failed for segment %d (attempt %d/%d): %s",
                    index, attempt, self.settings.translation_retries, exc,
                )
                if attempt < self.settings.translation_retries:
                    time.sleep(self.settings.translation_retry_delay_seconds)
        raise RuntimeError(f"Translation failed for segment {index}") from last_error
