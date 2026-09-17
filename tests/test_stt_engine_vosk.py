from __future__ import annotations

import sys
from types import SimpleNamespace

from src.stt_engine import STTEngine
from src.stt_engine_vosk import VoskSTTEngine


def test_vosk_engine_groups_words_after_silence() -> None:
    engine = object.__new__(VoskSTTEngine)
    engine.settings = SimpleNamespace(whisper_subtitle_split_silence_duration_ms=1000)

    result = engine._build_segments(
        [
            {"start": 0.0, "end": 0.4, "word": "hola"},
            {"start": 0.45, "end": 0.8, "word": "mundo"},
            {"start": 2.0, "end": 2.4, "word": "otra"},
        ]
    )

    assert result == [
        {"start": 0.0, "end": 0.8, "text": "hola mundo"},
        {"start": 2.0, "end": 2.4, "text": "otra"},
    ]


def test_x86_stt_engine_selects_vosk_on_windows(monkeypatch) -> None:
    class FakeVosk:
        def __init__(self, settings):
            self.settings = settings

        def transcribe(self, media_path):
            return [{"start": 0.0, "end": 1.0, "text": "hola"}]

    monkeypatch.setattr("src.stt_engine.struct.calcsize", lambda _: 4)
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "src.stt_engine_vosk", SimpleNamespace(VoskSTTEngine=FakeVosk))

    engine = STTEngine(SimpleNamespace())

    assert engine.device == "cpu"
    assert engine.compute_type == "int8"
    assert engine.transcribe("input.mp4") == [{"start": 0.0, "end": 1.0, "text": "hola"}]
