from pathlib import Path

from config.settings import AppSettings
from src.file_naming import normalize_component
from src.media_converter import MediaConverter


def test_settings_default_to_performance_oriented_values():
    settings = AppSettings()
    assert settings.whisper_beam_size == 1
    assert settings.whisper_condition_on_previous_text is False
    assert settings.translation_batch_size == 40
    assert settings.max_parallel_videos == 2
    assert settings.ffmpeg_avoid_reencode is True


def test_mp4_copy_command_avoids_reencode(tmp_path: Path):
    converter = MediaConverter(AppSettings())
    command = converter._build_mp4_copy_command(tmp_path / "in.mp4", tmp_path / "out.mp4")
    assert "-c" in command and "copy" in command
    assert "-movflags" in command and "+faststart" in command


def test_normalization_policy_is_wordpress_friendly():
    assert normalize_component("Vídeo niño — prueba") == "Video_nino_prueba"
