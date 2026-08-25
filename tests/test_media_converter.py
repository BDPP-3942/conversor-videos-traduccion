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


def test_secondary_video_command_is_lightweight_webm(tmp_path: Path) -> None:
    converter = MediaConverter(AppSettings())
    command = converter._build_secondary_video_command(tmp_path / "input.wmv", tmp_path / "result.webm")
    joined = " ".join(command)
    assert "libvpx" in joined
    assert "libopus" in joined
    assert "libvpx-vp9" in joined
    assert "-lossless 1" in joined
    assert "scale=" not in joined
    assert "-r" not in command


def test_secondary_video_command_supports_audio_only_sources(tmp_path: Path) -> None:
    converter = MediaConverter(AppSettings())
    command = converter._build_secondary_video_command(tmp_path / "input.mp3", tmp_path / "result.webm")
    joined = " ".join(command)
    assert "color=c=black" in joined
    assert "-shortest" in command
    assert "libvpx" in joined
    assert "libopus" in joined


def test_wmv_is_converted_to_mp4_and_webm(tmp_path: Path) -> None:
    source = tmp_path / "input.wmv"
    subprocess.run(
        [
            str(FFmpegResolver.resolve(AppSettings())),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=320x180:r=10",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:sample_rate=44100",
            "-t",
            "1",
            "-c:v",
            "wmv2",
            "-c:a",
            "wmav2",
            str(source),
        ],
        check=True,
    )
    artifacts = MediaConverter(AppSettings()).convert(source, "37x02_TEST", tmp_path / "out")
    assert artifacts.mp4_path.is_file()
    assert artifacts.secondary_video_path.is_file()
    assert artifacts.mp4_path.stat().st_size > 0
    assert artifacts.secondary_video_path.stat().st_size > 0


def test_mp4_uses_copy_path_when_enabled(tmp_path: Path) -> None:
    source = tmp_path / "input.mp4"
    subprocess.run(
        [
            str(FFmpegResolver.resolve(AppSettings())),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=320x180:r=10",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:sample_rate=44100",
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(source),
        ],
        check=True,
    )
    converter = MediaConverter(AppSettings())
    artifacts = converter.convert(source, "copy_test", tmp_path / "out")
    assert artifacts.mp4_path.is_file()
    assert artifacts.secondary_video_path.is_file()


def test_converter_can_skip_secondary_webm(tmp_path: Path) -> None:
    source = tmp_path / "input.mp4"
    source.write_bytes(b"not-real-video")
    converter = MediaConverter(AppSettings(generate_webm=False))

    # Avoid invoking FFmpeg for this focused configuration test.
    def fake_run(command):
        output = Path(command[-1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"output")

    converter._run = fake_run
    artifacts = converter.convert(source, "no_webm", tmp_path / "out")
    assert artifacts.mp4_path.name == "no_webm.mp4"
    assert artifacts.secondary_video_path is None


def test_converter_does_not_build_secondary_command_when_webm_disabled(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "input.mp4"
    source.write_bytes(b"not-real-video")
    converter = MediaConverter(AppSettings(generate_webm=False))
    calls = []

    def fake_run(command):
        calls.append(command)
        output = Path(command[-1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"output")

    monkeypatch.setattr(converter, "_run", fake_run)
    monkeypatch.setattr(
        converter, "_build_mp4_copy_command", lambda _source, output: ["ffmpeg", "mp4-copy", str(output)]
    )
    artifacts = converter.convert(source, "no_webm", tmp_path / "out")
    assert artifacts.secondary_video_path is None
    assert len(calls) == 1
