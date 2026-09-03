from types import SimpleNamespace

import pytest

from src import translation_providers


def test_local_provider_is_selected_for_supported_language_pair(monkeypatch) -> None:
    class FakeLocalProvider:
        pass

    monkeypatch.setattr(translation_providers, "AppSettings", SimpleNamespace)
    monkeypatch.setitem(__import__("sys").modules, "src.local_translation", SimpleNamespace(LocalTranslationProvider=FakeLocalProvider))
    settings = SimpleNamespace(source_lang="es", target_lang="en")
    provider = translation_providers.build_translation_provider("local", settings)
    assert isinstance(provider, FakeLocalProvider)


def test_local_provider_rejects_unsupported_language_pair() -> None:
    settings = SimpleNamespace(source_lang="es", target_lang="fr")
    with pytest.raises(ValueError, match="es→en"):
        translation_providers.build_translation_provider("local", settings)
