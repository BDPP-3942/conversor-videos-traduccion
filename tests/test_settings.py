from pathlib import Path

from config.loader import load_settings


def test_default_config_points_to_project_storage():
    settings = load_settings(Path("config/app.toml"))
    assert settings.provider == "local"
    assert settings.source == "local://storage/input"
    assert settings.target == "local://storage/output"


def test_auto_resources_are_applied_from_config():
    settings = load_settings(Path("config/app.toml"))
    assert settings.auto_tune_resources is True
    assert settings.whisper_model in {"small", "medium"}
    assert settings.whisper_cpu_threads >= 2
    assert settings.max_parallel_videos == 1


def test_automatic_output_deduplication_is_disabled_by_default():
    settings = load_settings(Path("config/app.toml"))
    assert settings.automatic_output_deduplication is False


def test_generate_webm_can_be_disabled_by_environment(monkeypatch):
    from config.settings import AppSettings

    monkeypatch.setenv("GENERATE_WEBM", "false")
    assert AppSettings.from_environment().generate_webm is False
