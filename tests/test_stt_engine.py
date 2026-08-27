from types import SimpleNamespace

from config.settings import AppSettings
from src.stt_engine import STTEngine


def _word(text: str, start: float, end: float):
    return SimpleNamespace(word=text, start=start, end=end)


def _segment(text: str, start: float, end: float, words):
    return SimpleNamespace(text=text, start=start, end=end, words=words)


def test_split_segment_preserves_a_long_internal_silence():
    engine = STTEngine.__new__(STTEngine)
    engine.settings = AppSettings(whisper_min_silence_duration_ms=750)
    segment = _segment(
        "Hola. Adiós.",
        1.0,
        6.0,
        [_word("Hola. ", 1.0, 1.5), _word("Adiós.", 4.0, 4.6)],
    )

    result = engine._split_segment_on_silence(segment)

    assert result == [
        {"start": 1.0, "end": 1.5, "text": "Hola."},
        {"start": 4.0, "end": 4.6, "text": "Adiós."},
    ]


def test_short_pause_does_not_split_a_whisper_segment():
    engine = STTEngine.__new__(STTEngine)
    engine.settings = AppSettings(whisper_min_silence_duration_ms=750)
    segment = _segment(
        "Hola mundo",
        1.0,
        3.0,
        [_word("Hola ", 1.0, 1.4), _word("mundo", 1.8, 2.2)],
    )

    result = engine._split_segment_on_silence(segment)

    assert result == [{"start": 1.0, "end": 2.2, "text": "Hola mundo"}]
