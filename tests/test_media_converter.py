import subprocess
from pathlib import Path

from config.settings import AppSettings
from src.ffmpeg_resolver import FFmpegResolver
from src.media_converter import MediaConverter


def test_mp3_source_gets_black_video_command(tmp_path: Path) -> None:
    source = tmp_path / "audio.mp3"
    output = tmp_path / "result.mp4"
    source.write_bytes(b"x")
    command = MediaConverter(AppSettings())._build_mp4_command(source, output)
    assert "lavfi" in command
    assert "black" in " ".join(command)
    assert str(source) in command


def test_wmv_is_converted_to_mp4_and_mp3(tmp_path: Path) -> None:
    source = tmp_path / "input.wmv"
    subprocess.run(
        [
            str(FFmpegResolver.resolve(AppSettings())), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=10",
            "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=44100",
            "-t", "1", "-c:v", "wmv2", "-c:a", "wmav2", str(source),
        ],
        check=True,
    )
    artifacts = MediaConverter(AppSettings()).convert(source, "37x02_TEST", tmp_path / "out")
    assert artifacts.mp4_path.is_file()
    assert artifacts.mp3_path.is_file()
    assert artifacts.mp4_path.stat().st_size > 0
    assert artifacts.mp3_path.stat().st_size > 0


def test_mp4_uses_copy_path_when_enabled(tmp_path: Path) -> None:
    source = tmp_path / "input.mp4"
    subprocess.run(
        [
            str(FFmpegResolver.resolve(AppSettings())), "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=10",
            "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=44100",
            "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(source),
        ],
        check=True,
    )
    converter = MediaConverter(AppSettings())
    artifacts = converter.convert(source, "copy_test", tmp_path / "out")
    assert artifacts.mp4_path.is_file()
    assert artifacts.mp3_path.is_file()
