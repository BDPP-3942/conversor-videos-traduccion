from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from config.settings import AppSettings
from src.tts_pipeline import TTSCue, _read_cues, _render_timeline


class FakeProvider:
    def __init__(self, durations: list[float]) -> None:
        self.durations = durations
        self.calls: list[tuple[str, float]] = []

    def synthesize(self, text: str, *, language: str, voice: str, speed: float):
        duration = self.durations[len(self.calls)]
        self.calls.append((text, speed))
        sample_rate = 1000
        return np.ones(round(duration * sample_rate), dtype=np.float32) * 0.2, sample_rate


def test_read_cues_preserves_timestamps_and_collapses_line_breaks(tmp_path: Path) -> None:
    path = tmp_path / "translated.vtt"
    path.write_text(
        "WEBVTT\n\n00:00:01.000 --> 00:00:03.500\nHola\nmundo\n\n00:00:05.000 --> 00:00:06.000\nAdiós\n",
        encoding="utf-8",
    )

    cues = _read_cues(path)

    assert cues == [TTSCue(1.0, 3.5, "Hola mundo"), TTSCue(5.0, 6.0, "Adiós")]


def test_render_timeline_keeps_silence_between_cues(tmp_path: Path) -> None:
    provider = FakeProvider([0.5, 0.5])
    settings = AppSettings(tts_sample_rate=1000, tts_duration_tolerance=0.02)
    output = tmp_path / "tts.wav"

    adjusted = _render_timeline(
        [TTSCue(1.0, 2.0, "Uno"), TTSCue(4.0, 5.0, "Dos")],
        provider,
        settings,
        output,
    )

    assert adjusted == 0
    assert output.is_file()
    assert provider.calls[0] == ("Uno", 1.0)
    assert provider.calls[1] == ("Dos", 1.0)


def test_render_timeline_retries_with_higher_speed_when_cue_is_too_long(tmp_path: Path) -> None:
    provider = FakeProvider([1.2, 0.9])
    settings = AppSettings(tts_sample_rate=1000, tts_speed=1.0, tts_max_speed=1.35)
    output = tmp_path / "tts.wav"

    adjusted = _render_timeline(
        [TTSCue(0.0, 1.0, "Texto")],
        provider,
        settings,
        output,
    )

    assert adjusted == 1
    assert len(provider.calls) == 2
    assert provider.calls[0] == ("Texto", 1.0)
    assert provider.calls[1][0] == "Texto"
    assert 1.0 < provider.calls[1][1] <= 1.35


def test_render_timeline_time_stretches_when_max_speed_is_insufficient(tmp_path: Path, monkeypatch) -> None:
    provider = FakeProvider([2.0, 2.0, 0.5])
    settings = AppSettings(tts_sample_rate=1000, tts_speed=1.0, tts_max_speed=1.1)
    output = tmp_path / "tts.wav"
    stretch_calls: list[tuple[int, int]] = []

    def fake_time_stretch(samples, target_samples, sample_rate, settings, temp_dir):
        stretch_calls.append((len(samples), target_samples))
        return np.ones(target_samples, dtype=np.float32) * 0.2

    monkeypatch.setattr("src.tts_pipeline._time_stretch_to_fit", fake_time_stretch)
    adjusted = _render_timeline(
        [TTSCue(0.0, 1.0, "Texto"), TTSCue(1.0, 2.0, "Siguiente")],
        provider,
        settings,
        output,
    )

    assert adjusted == 2
    assert stretch_calls == [(2000, 1000)]
    assert len(provider.calls) == 3
    assert output.is_file()


def test_render_timeline_still_rejects_unrecoverable_stretch_failure(tmp_path: Path, monkeypatch) -> None:
    provider = FakeProvider([2.0])
    settings = AppSettings(tts_sample_rate=1000, tts_speed=1.0, tts_max_speed=1.1)
    output = tmp_path / "tts.wav"

    def failing_stretch(*args):
        raise RuntimeError("FFmpeg unavailable")

    monkeypatch.setattr("src.tts_pipeline._time_stretch_to_fit", failing_stretch)
    with pytest.raises(RuntimeError, match="FFmpeg unavailable"):
        _render_timeline([TTSCue(0.0, 1.0, "Texto")], provider, settings, output)
