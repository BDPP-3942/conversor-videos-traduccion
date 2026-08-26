from pathlib import Path

import pytest

from config.settings import AppSettings
from src.media_converter import MEDIA_EXTENSIONS, MediaConverter


@pytest.mark.parametrize("extension", [".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv"])
def test_advertised_raw_video_extension_is_supported(extension: str) -> None:
    assert extension in MEDIA_EXTENSIONS


def test_converter_accepts_advertised_raw_video_extension(tmp_path: Path) -> None:
    source = tmp_path / "input.webm"
    source.write_bytes(b"not-real-video")
    converter = MediaConverter(AppSettings(generate_webm=False))

    def fake_run(command: list[str]) -> None:
        output = Path(command[-1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"output")

    converter._run = fake_run
    artifacts = converter.convert(source, "raw_webm", tmp_path / "out")
    assert artifacts.mp4_path.name == "raw_webm.mp4"
