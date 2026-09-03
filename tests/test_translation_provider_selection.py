from types import SimpleNamespace

import pytest

from src import translation_providers
from src.translation_providers import TranslationConfigurationError


class FakeLocalProvider:
    def __init__(self, settings):
        self.settings = settings


def test_local_provider_is_selected_for_supported_language_pair(monkeypatch) -> None:
    monkeypatch.setattr(translation_providers, "AppSettings", SimpleNamespace)
    monkeypatch.setitem(
        __import__("sys").modules,
        "src.local_translation",
        SimpleNamespace(LocalTranslationProvider=FakeLocalProvider),
    )
    settings = SimpleNamespace(source_lang="es", target_lang="en")
    provider = translation_providers.build_translation_provider("local", settings)
    assert isinstance(provider, FakeLocalProvider)
    assert provider.settings is settings


def test_local_provider_rejects_unsupported_language_pair() -> None:
    settings = SimpleNamespace(source_lang="es", target_lang="fr")
    with pytest.raises(TranslationConfigurationError, match="es→en"):
        translation_providers.build_translation_provider("local", settings)
