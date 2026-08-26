from __future__ import annotations

import os

import pytest

from config.settings import AppSettings
from src.translation_providers import (
    DeepLBatchProvider,
    GoogleCloudBatchProvider,
    MicrosoftBatchProvider,
    MyMemoryBatchProvider,
    build_translation_provider,
)


def test_google_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_TRANSLATE_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GOOGLE_TRANSLATE_API_KEY"):
        build_translation_provider("google", AppSettings())


def test_google_builds_official_api_client(monkeypatch):
    monkeypatch.setenv("GOOGLE_TRANSLATE_API_KEY", "test-key")
    provider = build_translation_provider(
        "google", AppSettings(source_lang="es", target_lang="en")
    )

    assert isinstance(provider, GoogleCloudBatchProvider)
    assert provider.source == "es"
    assert provider.target == "en"
    assert provider.api_key == "test-key"


def test_deepl_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("DEEPL_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="DEEPL_API_KEY"):
        build_translation_provider("deepl", AppSettings())


def test_deepl_builds_direct_api_client(monkeypatch):
    monkeypatch.setenv("DEEPL_API_KEY", "test-key")
    provider = build_translation_provider("deepl", AppSettings())

    assert isinstance(provider, DeepLBatchProvider)
    assert provider.source == "ES"
    assert provider.target == "EN"
    assert provider.api_key == "test-key"


def test_microsoft_requires_an_api_key(monkeypatch):
    monkeypatch.delenv("MICROSOFT_TRANSLATOR_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="MICROSOFT_TRANSLATOR_API_KEY"):
        build_translation_provider("microsoft", AppSettings())


def test_microsoft_builds_direct_api_client(monkeypatch):
    monkeypatch.setenv("MICROSOFT_TRANSLATOR_API_KEY", "test-key")
    monkeypatch.setenv("MICROSOFT_TRANSLATOR_REGION", "westeurope")
    provider = build_translation_provider("microsoft", AppSettings())

    assert isinstance(provider, MicrosoftBatchProvider)
    assert provider.source == "es"
    assert provider.target == "en"
    assert provider.api_key == "test-key"
    assert provider.region == "westeurope"


def test_mymemory_requires_no_credentials(monkeypatch):
    monkeypatch.delenv("LIBRETRANSLATE_API_KEY", raising=False)
    provider = build_translation_provider(
        "mymemory", AppSettings(source_lang="spanish", target_lang="english")
    )

    assert isinstance(provider, MyMemoryBatchProvider)
    assert provider.source == "es"
    assert provider.target == "en"


def test_direct_clients_do_not_depend_on_deep_translator(monkeypatch):
    monkeypatch.setitem(os.environ, "GOOGLE_TRANSLATE_API_KEY", "test-key")
    monkeypatch.setitem(os.environ, "DEEPL_API_KEY", "test-key")
    monkeypatch.setitem(os.environ, "MICROSOFT_TRANSLATOR_API_KEY", "test-key")

    for name, expected in (
        ("google", GoogleCloudBatchProvider),
        ("deepl", DeepLBatchProvider),
        ("microsoft", MicrosoftBatchProvider),
        ("mymemory", MyMemoryBatchProvider),
    ):
        assert isinstance(build_translation_provider(name, AppSettings()), expected)
