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
