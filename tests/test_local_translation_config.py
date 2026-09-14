from pathlib import Path

import config.loader as loader
from config.loader import load_settings


def test_default_madlad_model_configuration_matches_pinned_definition(monkeypatch) -> None:
    monkeypatch.setattr(loader, "_load_dotenv", lambda: None)
    for name in (
        "LOCAL_TRANSLATION_MODEL",
        "LOCAL_TRANSLATION_MODEL_DIR",
        "LOCAL_TRANSLATION_MODEL_ID",
        "LOCAL_TRANSLATION_MODEL_REVISION",
        "LOCAL_TRANSLATION_DEVICE",
        "LOCAL_TRANSLATION_COMPUTE_TYPE",
        "LOCAL_TRANSLATION_BEAM_SIZE",
        "LOCAL_TRANSLATION_AUTO_DOWNLOAD",
        "LOCAL_TRANSLATION_HF_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = load_settings(Path("config/app.toml"))
    assert settings.local_translation_model == "madlad400-3b-ct2-int8"
    assert settings.local_translation_model_id == "cstr/madlad400-3b-ct2-int8"
    assert settings.local_translation_model_revision == "fd0b55729c074372eb84b52b9309a00dc65c40c4"


def test_local_translation_model_configuration_is_loaded_from_toml(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(loader, "_load_dotenv", lambda: None)
    for name in (
        "LOCAL_TRANSLATION_MODEL",
        "LOCAL_TRANSLATION_MODEL_DIR",
        "LOCAL_TRANSLATION_MODEL_ID",
        "LOCAL_TRANSLATION_MODEL_REVISION",
        "LOCAL_TRANSLATION_DEVICE",
        "LOCAL_TRANSLATION_COMPUTE_TYPE",
        "LOCAL_TRANSLATION_BEAM_SIZE",
        "LOCAL_TRANSLATION_AUTO_DOWNLOAD",
        "LOCAL_TRANSLATION_HF_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)

    config = tmp_path / "app.toml"
    config.write_text(
        """
[processing]
local_translation_model = "opus-mt-es-en-ct2-int8"
local_translation_model_dir = "tools/models/translation/opus-mt-es-en-ct2-int8"
local_translation_model_id = "Prukario/opus-mt-es-en-ct2-int8"
local_translation_model_revision = "ad91ad1697ea1761111ff4c179400796d085b347"
local_translation_device = "cpu"
local_translation_compute_type = "int8"
local_translation_beam_size = 3
local_translation_auto_download = false
""",
        encoding="utf-8",
    )
    settings = load_settings(config)
    assert settings.local_translation_model == "opus-mt-es-en-ct2-int8"
    assert settings.local_translation_model_dir == Path("tools/models/translation/opus-mt-es-en-ct2-int8")
    assert settings.local_translation_model_id == "Prukario/opus-mt-es-en-ct2-int8"
    assert settings.local_translation_model_revision == "ad91ad1697ea1761111ff4c179400796d085b347"
    assert settings.local_translation_device == "cpu"
    assert settings.local_translation_compute_type == "int8"
    assert settings.local_translation_beam_size == 3
    assert settings.local_translation_auto_download is False
