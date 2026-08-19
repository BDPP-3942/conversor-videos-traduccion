from pathlib import Path

import pytest

webvtt = pytest.importorskip("webvtt")
from src.vtt_builder import VTTBuilder  # noqa: E402


def test_negative_time_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        VTTBuilder.generate_vtt([{"start": -1, "end": 1, "text": "bad"}], tmp_path / "out.vtt")


def test_invalid_interval_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        VTTBuilder.generate_vtt([{"start": 2, "end": 1, "text": "bad"}], tmp_path / "out.vtt")
