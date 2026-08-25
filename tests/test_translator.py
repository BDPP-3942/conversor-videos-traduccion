from __future__ import annotations

import logging

from config.settings import AppSettings
from src.translator import TextTranslator


class WorkingTranslator:
    def __init__(self, prefix: str = "EN"):
        self.prefix = prefix
        self.batch_calls = 0

    def translate_batch(self, texts):
        self.batch_calls += 1
        return [f"{self.prefix}:{text}" for text in texts]

    def translate(self, text):
        return f"{self.prefix}:{text}"


class AlwaysFailTranslator:
    def __init__(self, error: str = "provider unavailable"):
        self.error = error
        self.batch_calls = 0

    def translate_batch(self, texts):
        self.batch_calls += 1
        raise RuntimeError(self.error)

    def translate(self, text):
        raise RuntimeError(self.error)


class PartialTranslator:
    def translate_batch(self, texts):
        return [f"EN:{text}" if text != "dos" else "" for text in texts]

    def translate(self, text):
        return f"EN:{text}"


def _translator(settings: AppSettings, providers: dict[str, object]) -> TextTranslator:
    translator = TextTranslator(settings)
    translator._providers = providers
    return translator


def test_primary_provider_works(monkeypatch):
    settings = AppSettings(
        translation_provider="google",
        translation_fallback_providers=("microsoft",),
        translation_max_retries_per_provider=2,
        translation_batch_size=2,
        translation_min_request_interval_seconds=0,
        translation_retry_delay_seconds=0,
    )
    primary = WorkingTranslator()
    translator = _translator(settings, {"google": primary})
    monkeypatch.setattr(translator, "_get_provider", lambda name: translator._providers[name])

    result = translator.translate_segments(
        [{"start": 0, "end": 1, "text": "uno"}, {"start": 1, "end": 2, "text": "dos"}]
    )

    assert [item["text"] for item in result] == ["EN:uno", "EN:dos"]
    assert all(item["translation_provider"] == "google" for item in result)


def test_first_provider_fails_and_second_works(monkeypatch, caplog):
    settings = AppSettings(
        translation_provider="google",
        translation_fallback_providers=("microsoft",),
        translation_max_retries_per_provider=3,
        translation_batch_size=2,
        translation_min_request_interval_seconds=0,
        translation_retry_delay_seconds=0,
    )
    first = AlwaysFailTranslator("google outage")
    second = WorkingTranslator()
    translator = _translator(settings, {"google": first, "microsoft": second})
    monkeypatch.setattr(translator, "_get_provider", lambda name: translator._providers[name])

    with caplog.at_level(logging.INFO):
        result = translator.translate_segments([{"start": 0, "end": 1, "text": "uno"}])

    assert result[0]["text"] == "EN:uno"
    assert result[0]["translation_provider"] == "microsoft"
    assert first.batch_calls == 3
    assert second.batch_calls == 1
    assert "Switching translation provider from 'google' to 'microsoft'" in caplog.text


def test_first_provider_fails_partially_and_fallback_only_handles_failed_segments(monkeypatch):
    settings = AppSettings(
        translation_provider="google",
        translation_fallback_providers=("microsoft",),
        translation_max_retries_per_provider=2,
        translation_batch_size=2,
        translation_min_request_interval_seconds=0,
        translation_retry_delay_seconds=0,
    )
    first = PartialTranslator()
    second = WorkingTranslator()
    translator = _translator(settings, {"google": first, "microsoft": second})
    monkeypatch.setattr(translator, "_get_provider", lambda name: translator._providers[name])

    result = translator.translate_segments(
        [
            {"start": 0, "end": 1, "text": "uno"},
            {"start": 1, "end": 2, "text": "dos"},
        ]
    )

    assert [item["text"] for item in result] == ["EN:uno", "EN:dos"]
    assert result[0]["translation_provider"] == "google"
    assert result[1]["translation_provider"] == "microsoft"


def test_fallback_preserves_successful_segments_when_all_providers_do_not_succeed(monkeypatch):
    settings = AppSettings(
        translation_provider="google",
        translation_fallback_providers=("microsoft",),
        translation_max_retries_per_provider=1,
        translation_batch_size=2,
        translation_min_request_interval_seconds=0,
        translation_retry_delay_seconds=0,
    )
    first = PartialTranslator()
    second = AlwaysFailTranslator()
    translator = _translator(settings, {"google": first, "microsoft": second})
    monkeypatch.setattr(translator, "_get_provider", lambda name: translator._providers[name])

    result = translator.translate_segments(
        [
            {"start": 0, "end": 1, "text": "uno"},
            {"start": 1, "end": 2, "text": "dos"},
        ]
    )

    assert result[0]["text"] == "EN:uno"
    assert result[0]["translation_failed"] is not True
    assert result[1]["text"] == "dos"
    assert result[1]["translation_failed"] is True
    assert "microsoft" in result[1]["translation_errors"][0]


def test_all_providers_fail_without_infinite_retry(monkeypatch):
    settings = AppSettings(
        translation_provider="google",
        translation_fallback_providers=("microsoft", "libretranslate"),
        translation_max_retries_per_provider=2,
        translation_batch_size=1,
        translation_min_request_interval_seconds=0,
        translation_retry_delay_seconds=0,
    )
    providers = {
        "google": AlwaysFailTranslator("google failed"),
        "microsoft": AlwaysFailTranslator("microsoft failed"),
        "libretranslate": AlwaysFailTranslator("libre failed"),
    }
    translator = _translator(settings, providers)
    monkeypatch.setattr(translator, "_get_provider", lambda name: translator._providers[name])

    result = translator.translate_segments([{"start": 0, "end": 1, "text": "uno"}])

    assert result[0]["text"] == "uno"
    assert result[0]["translation_failed"] is True
    assert all(provider.batch_calls == 2 for provider in providers.values())


def test_existing_translation_retry_setting_remains_compatible(monkeypatch):
    settings = AppSettings(
        translation_provider="google",
        translation_retries=4,
        translation_batch_size=1,
        translation_min_request_interval_seconds=0,
        translation_retry_delay_seconds=0,
    )
    provider = AlwaysFailTranslator()
    translator = _translator(settings, {"google": provider})
    monkeypatch.setattr(translator, "_get_provider", lambda name: translator._providers[name])

    result = translator.translate_segments([{"start": 0, "end": 1, "text": "uno"}])

    assert result[0]["translation_failed"] is True
    assert provider.batch_calls == 4
