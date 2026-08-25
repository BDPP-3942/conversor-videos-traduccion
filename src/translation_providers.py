from __future__ import annotations

import os
from typing import Protocol

from config.settings import AppSettings


class TranslationProvider(Protocol):
    """Minimal interface required by the translation pipeline."""

    def translate_batch(self, texts: list[str]) -> list[str]: ...

    def translate(self, text: str) -> str: ...


def build_translation_provider(name: str, settings: AppSettings) -> TranslationProvider:
    """Build one of the providers already supported by deep-translator."""
    provider = name.strip().lower().replace("-", "_")
    try:
        from deep_translator import GoogleTranslator, LibreTranslator, MicrosoftTranslator
    except ImportError as exc:
        raise RuntimeError("Translation support requires the deep-translator package") from exc

    if provider == "google":
        return GoogleTranslator(source=settings.source_lang, target=settings.target_lang)
    if provider == "microsoft":
        api_key = os.getenv("MICROSOFT_TRANSLATOR_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("Microsoft translation provider requires MICROSOFT_TRANSLATOR_API_KEY")
        return MicrosoftTranslator(
            source=settings.source_lang,
            target=settings.target_lang,
            api_key=api_key,
        )
    if provider in {"libretranslate", "libre"}:
        return LibreTranslator(source=settings.source_lang, target=settings.target_lang)
    raise ValueError(f"Unsupported translation provider: {name}")
