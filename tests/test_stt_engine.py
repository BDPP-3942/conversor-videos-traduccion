from pathlib import Path
from types import SimpleNamespace

from config.settings import AppSettings
from src.stt_engine import STTEngine
from src.stt_quality import STTQualityThresholds


def _word(text: str, start: float, end: float):
    return SimpleNamespace(word=text, start=start, end=end)


def _segment(text: str, start: float, end: float, words, **metrics):
    return SimpleNamespace(text=text, start=start, end=end, words=words, **metrics)


def _recovery_engine(model, retries=1, temperatures=(0.2,)):
    engine = STTEngine.__new__(STTEngine)
    engine.settings = AppSettings(
        whisper_recovery_retries=retries,
        whisper_recovery_temperatures=temperatures,
    )
    engine._quality_thresholds = STTQualityThresholds()
    engine.model = model
    engine.device = "cpu"
    engine.compute_type = "int8"
    return engine


def test_split_segment_uses_independent_subtitle_silence_threshold():
    engine = STTEngine.__new__(STTEngine)
    engine.settings = AppSettings(
        whisper_min_silence_duration_ms=1500,
        whisper_subtitle_split_silence_duration_ms=750,
    )
    segment = _segment(
        "Hola. Adiós.",
        1.0,
        6.0,
        [_word("Hola. ", 1.0, 1.5), _word("Adiós.", 4.0, 4.6)],
    )

    assert engine._split_segment_on_silence(segment) == [
        {"start": 1.0, "end": 1.5, "text": "Hola."},
        {"start": 4.0, "end": 4.6, "text": "Adiós."},
    ]


def test_short_pause_does_not_split_a_whisper_segment():
    engine = STTEngine.__new__(STTEngine)
    engine.settings = AppSettings(whisper_subtitle_split_silence_duration_ms=750)
    segment = _segment(
        "Hola mundo",
        1.0,
        3.0,
        [_word("Hola ", 1.0, 1.4), _word("mundo", 1.8, 2.2)],
    )

    assert engine._split_segment_on_silence(segment) == [{"start": 1.0, "end": 2.2, "text": "Hola mundo"}]


def test_recovery_retries_zero_disables_recovery():
    calls = []

    class Model:
        def transcribe(self, *args, **kwargs):
            calls.append(kwargs)
            return ([], None)

    engine = _recovery_engine(Model(), retries=0)
    segment = _segment("Pong " * 12, 1.0, 2.0, [])

    assert engine._recover_segment(Path("input.mp4"), segment) == []
    assert calls == []


def test_recovery_retry_is_limited_by_whisper_recovery_retries_and_drops_prompt_in_context_free_pass():
    calls = []

    class Model:
        def transcribe(self, *args, **kwargs):
            calls.append(kwargs)
            return ([_segment("Pong " * 12, 1.0, 2.0, [])], None)

    engine = _recovery_engine(Model(), retries=2, temperatures=(0.2, 0.4))
    assert engine._recover_segment(Path("input.mp4"), _segment("Pong " * 12, 1.0, 2.0, [])) == []
    assert len(calls) == 4
    assert [call["temperature"] for call in calls] == [0.2, 0.2, 0.4, 0.4]
    assert [call["condition_on_previous_text"] for call in calls] == [True, False, True, False]
    assert all(call["clip_timestamps"] == [1.0, 2.0] for call in calls)
    assert "initial_prompt" not in calls[1]
    assert "initial_prompt" not in calls[3]


def test_recovery_stops_after_a_healthy_context_preserving_attempt():
    calls = []
    healthy = _segment("Pong Yang, expansión y continuidad", 1.0, 2.0, [])
    bad = _segment("Pong " * 12, 1.0, 2.0, [])

    class Model:
        def transcribe(self, *args, **kwargs):
            calls.append(kwargs)
            return ([healthy if kwargs["condition_on_previous_text"] else bad], None)

    engine = _recovery_engine(Model(), retries=3, temperatures=(0.2, 0.4, 0.6))
    assert engine._recover_segment(Path("input.mp4"), bad) == [healthy]
    assert len(calls) == 1
    assert calls[0]["condition_on_previous_text"] is True
    assert calls[0]["temperature"] == 0.2


def test_recovery_passes_numeric_clip_timestamps_to_transcribe():
    calls = []
    healthy = _segment("Texto recuperado", 1.25, 2.75, [])

    class Model:
        def transcribe(self, *args, **kwargs):
            calls.append(kwargs)
            clip_timestamps = kwargs["clip_timestamps"]
            assert clip_timestamps == [1.25, 2.75]
            assert all(isinstance(value, (int, float)) for value in clip_timestamps)
            assert not any(isinstance(value, dict) for value in clip_timestamps)
            return ([healthy], None)

    engine = _recovery_engine(Model())
    suspicious = _segment("Pong " * 12, 1.25, 2.75, [])

    assert engine._recover_segment(Path("input.mp4"), suspicious) == [healthy]
    assert len(calls) == 1


def test_normal_transcription_does_not_use_clip_timestamps():
    calls = []
    normal = _segment("Hola mundo", 0.0, 1.5, [])

    class Model:
        def transcribe(self, *args, **kwargs):
            calls.append(kwargs)
            assert "clip_timestamps" not in kwargs
            return ([normal], None)

    engine = _recovery_engine(Model())
    assert engine.transcribe(Path("input.mp4")) == [{"start": 0.0, "end": 1.5, "text": "Hola mundo"}]
    assert len(calls) == 1


def test_recovery_preserves_recovered_timestamps_and_text():
    recovered = _segment(
        "Hola. Adiós.",
        1.0,
        5.0,
        [_word("Hola. ", 1.0, 1.4), _word("Adiós.", 4.0, 4.5)],
    )
    calls = []

    class Model:
        def transcribe(self, *args, **kwargs):
            calls.append(kwargs)
            return ([recovered], None)

    engine = _recovery_engine(Model())
    suspicious = _segment("Pong " * 12, 1.0, 5.0, [])

    assert engine._recover_segment(Path("input.mp4"), suspicious) == [recovered]
    assert calls[0]["clip_timestamps"] == [1.0, 5.0]
    assert engine._split_segment_on_silence(recovered) == [
        {"start": 1.0, "end": 1.4, "text": "Hola."},
        {"start": 4.0, "end": 4.5, "text": "Adiós."},
    ]
