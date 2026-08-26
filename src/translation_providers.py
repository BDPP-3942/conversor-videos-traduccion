from __future__ import annotations

import os
from typing import Protocol

from config.settings import AppSettings


class TranslationProvider(Protocol):
    """Minimal interface required by the translation pipeline."""

    def translate_batch(self, texts: list[str]) -> list[str]: ...

    def translate(self, text: str) -> str: ...


def _mymemory_language(language: str, languages: dict[str, str]) -> str:
    """Return a language identifier accepted by MyMemory's deep-translator adapter.

    The rest of the application intentionally uses compact ISO-639-1 values such as
    ``es`` and ``en``. MyMemory's language table uses locale values (for example
    ``es-ES`` and ``en-GB``) and therefore rejects those compact values before any
    HTTP request is made. Prefer an exact supported value, then a named language,
    and finally the first locale matching the requested two-letter code.
    """
    value = str(language).strip()
    if value == "auto":
        return value
    if value in languages.values():
        return value
    if value in languages:
        return languages[value]
    prefix = f"{value.lower()}-"
    for code in languages.values():
        if str(code).lower().startswith(prefix):
            return code
    raise ValueError(f"MyMemory does not support configured language {language!r}")


def build_translation_provider(name: str, settings: AppSettings) -> TranslationProvider:
    """Build a configured provider supported by the existing deep-translator dependency."""
    provider = name.strip().lower().replace("-", "_")
    try:
        from deep_translator import GoogleTranslator, LibreTranslator, MicrosoftTranslator, MyMemoryTranslator
    except ImportError as exc:
        raise RuntimeError("Translation support requires the deep-translator package") from exc

    if provider == "google":
        return GoogleTranslator(source=settings.source_lang, target=settings.target_lang)
    if provider in {"mymemory", "my_memory"}:
        try:
            from deep_translator.constants import MY_MEMORY_LANGUAGES_TO_CODES
        except ImportError as exc:
            raise RuntimeError("Installed deep-translator version does not expose MyMemory language metadata") from exc
        source = _mymemory_language(settings.source_lang, MY_MEMORY_LANGUAGES_TO_CODES)
        target = _mymemory_language(settings.target_lang, MY_MEMORY_LANGUAGES_TO_CODES)
        return MyMemoryTranslator(source=source, target=target)
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
        api_key = os.getenv("LIBRETRANSLATE_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "LibreTranslate provider requires LIBRETRANSLATE_API_KEY with the current deep-translator API"
            )
        custom_url = os.getenv("LIBRETRANSLATE_URL", "").strip() or None
        return LibreTranslator(
            source=settings.source_lang,
            target=settings.target_lang,
            api_key=api_key,
            custom_url=custom_url,
        )
    raise ValueError(f"Unsupported translation provider: {name}")
