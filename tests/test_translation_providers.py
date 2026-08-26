from __future__ import annotations

import sys
import types

import pytest

from config.settings import AppSettings
from src.translation_providers import build_translation_provider


def _fake_deep_translator(monkeypatch):
    module = types.ModuleType("deep_translator")

    class GoogleTranslator:
        def __init__(self, source, target):
            self.source = source
            self.target = target

    class MyMemoryTranslator:
        def __init__(self, source, target):
            self.source = source
            self.target = target

    class MicrosoftTranslator:
        def __init__(self, source, target, api_key):
            self.source = source
            self.target = target
            self.api_key = api_key

    class LibreTranslator:
        def __init__(self, source, target, api_key, custom_url=None):
            self.source = source
            self.target = target
            self.api_key = api_key
            self.custom_url = custom_url

    module.GoogleTranslator = GoogleTranslator
    module.MyMemoryTranslator = MyMemoryTranslator
    module.MicrosoftTranslator = MicrosoftTranslator
    module.LibreTranslator = LibreTranslator
    monkeypatch.setitem(sys.modules, "deep_translator", module)
    return module


def _fake_mymemory_constants(monkeypatch):
    constants = types.ModuleType("deep_translator.constants")
    constants.MY_MEMORY_LANGUAGES_TO_CODES = {
        "spanish": "es-ES",
        "english": "en-GB",
    }
    monkeypatch.setitem(sys.modules, "deep_translator.constants", constants)


def test_mymemory_is_a_no_key_provider(monkeypatch):
    _fake_deep_translator(monkeypatch)
    _fake_mymemory_constants(monkeypatch)
    provider = build_translation_provider("mymemory", AppSettings(source_lang="es", target_lang="en"))

    assert provider.source == "es-ES"
    assert provider.target == "en-GB"


def test_mymemory_accepts_named_languages(monkeypatch):
    _fake_deep_translator(monkeypatch)
    _fake_mymemory_constants(monkeypatch)
    provider = build_translation_provider("mymemory", AppSettings(source_lang="spanish", target_lang="english"))

    assert provider.source == "es-ES"
    assert provider.target == "en-GB"


def test_microsoft_requires_an_api_key(monkeypatch):
    _fake_deep_translator(monkeypatch)
    monkeypatch.delenv("MICROSOFT_TRANSLATOR_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="MICROSOFT_TRANSLATOR_API_KEY"):
        build_translation_provider("microsoft", AppSettings())


def test_libretranslate_is_optional_and_requires_explicit_credentials(monkeypatch):
    _fake_deep_translator(monkeypatch)
    monkeypatch.delenv("LIBRETRANSLATE_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="LIBRETRANSLATE_API_KEY"):
        build_translation_provider("libretranslate", AppSettings())


def test_libretranslate_can_be_configured_with_key_and_endpoint(monkeypatch):
    _fake_deep_translator(monkeypatch)
    monkeypatch.setenv("LIBRETRANSLATE_API_KEY", "test-key")
    monkeypatch.setenv("LIBRETRANSLATE_URL", "https://example.invalid/")

    provider = build_translation_provider("libretranslate", AppSettings())

    assert provider.api_key == "test-key"
    assert provider.custom_url == "https://example.invalid/"
