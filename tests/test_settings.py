from pathlib import Path

from config.loader import load_settings


def test_default_config_points_to_project_storage():
    settings = load_settings(Path("config/app.toml"))
    assert settings.provider == "local"
    assert settings.source == "local://storage/input"
    assert settings.target == "local://storage/output"
