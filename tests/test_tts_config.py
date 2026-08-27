from __future__ import annotations

from pathlib import Path

from config.loader import load_settings


def test_tts_is_disabled_by_default() -> None:
    settings = load_settings(Path("config/app.toml"))

    assert settings.tts_enabled is False
    assert settings.tts_required is False
    assert settings.tts_provider == "kokoro"
    assert settings.tts_voice == "af_sarah"
    assert settings.tts_generate_webm is True
