from pathlib import Path

from config.settings import AppSettings
from src.file_naming import normalize_component
from src.media_converter import MediaConverter


def test_settings_default_to_performance_oriented_values():
    settings = AppSettings()
    assert settings.whisper_beam_size == 5
    assert settings.whisper_condition_on_previous_text is True
    assert settings.translation_batch_size == 25
    assert settings.max_parallel_videos == 0
    assert settings.ffmpeg_avoid_reencode is True
    assert settings.generate_webm is True
    assert settings.ffmpeg_preset == "medium"
    assert settings.ffmpeg_crf == 23
    assert settings.ffmpeg_audio_bitrate == "256k"
    assert settings.secondary_video_extension == "webm"
    assert settings.secondary_video_codec == "libvpx-vp9"
    assert settings.secondary_video_crf == 0
    assert settings.secondary_video_max_width == 0
    assert settings.secondary_video_fps == 0
    assert settings.secondary_video_audio_bitrate == "256k"


def test_mp4_copy_command_avoids_reencode(tmp_path: Path):
    converter = MediaConverter(AppSettings())
    command = converter._build_mp4_copy_command(tmp_path / "in.mp4", tmp_path / "out.mp4")
    assert "-c" in command and "copy" in command
    assert "-movflags" in command and "+faststart" in command


def test_normalization_policy_preserves_unicode_and_is_filesystem_safe():
    assert normalize_component("Vídeo niño — prueba") == "Vídeo_niño_prueba"


def test_resource_profile_keeps_medium_for_high_end_hardware(monkeypatch):
    monkeypatch.setattr("src.resource_profile._memory_gb", lambda: 32.0)
    monkeypatch.setattr("src.resource_profile.os.cpu_count", lambda: 16)
    profile = __import__("src.resource_profile", fromlist=["detect_profile"]).detect_profile(AppSettings())
    assert profile.name == "high"
    assert profile.whisper_model == "medium"
    assert profile.max_parallel_videos == 1


def test_resource_profile_uses_small_on_8gb_class_machine(monkeypatch):
    monkeypatch.setattr("src.resource_profile._memory_gb", lambda: 8.0)
    monkeypatch.setattr("src.resource_profile.os.cpu_count", lambda: 4)
    profile = __import__("src.resource_profile", fromlist=["detect_profile"]).detect_profile(AppSettings())
    assert profile.name == "low"
    assert profile.whisper_threads <= 4
