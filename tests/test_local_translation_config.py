from pathlib import Path

from config.loader import load_settings


def test_local_translation_model_configuration_is_loaded_from_toml(tmp_path: Path) -> None:
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
