from pathlib import Path

from config.settings import AppSettings, BASE_DIR
from src.ffmpeg_resolver import FFmpegResolver


def test_ffmpeg_resolves_from_project_or_python_environment():
    result = FFmpegResolver.resolve(AppSettings())
    assert result.is_file()


def test_explicit_relative_binary_path_is_resolved(tmp_path: Path, monkeypatch):
    binary = tmp_path / ("ffmpeg.exe" if __import__("sys").platform.startswith("win") else "ffmpeg")
    binary.write_bytes(b"fake")
    settings = AppSettings(ffmpeg_bin=str(binary))
    assert FFmpegResolver.resolve(settings) == binary.resolve()


def test_local_original_transcriptions_are_inside_video_output():
    from src.storage.local import LocalStorageProvider

    provider = LocalStorageProvider(retain_sources=False, input_min_age_seconds=0)
    output = provider.ensure_folder("storage/output", "sample_video")
    original = provider.ensure_folder(output, "original_transcriptions")
    assert original.endswith("sample_video\\original_transcriptions") or original.endswith("sample_video/original_transcriptions")
