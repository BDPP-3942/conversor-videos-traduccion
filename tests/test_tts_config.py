from __future__ import annotations

from pathlib import Path

from config.loader import load_settings


def test_tts_is_disabled_by_default() -> None:
    settings = load_settings(Path("config/app.toml"))

    assert settings.tts_enabled is False
    assert settings.tts_required is False
    assert settings.tts_provider == "kokoro"
    assert settings.tts_voice == "am_michael"
    assert settings.tts_generate_webm is False

def test_webm_generation_is_disabled_by_default():
    settings = load_settings(Path("config/app.toml"))
    assert settings.generate_webm is False
