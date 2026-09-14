import threading

import pytest

from src.controllable_pipeline import ControllableMediaPipeline, PipelineCancelled


def test_check_cancelled_emits_event():
    events = []
    cancel_event = threading.Event()
    cancel_event.set()
    pipeline = object.__new__(ControllableMediaPipeline)
    pipeline.event_callback = events.append
    pipeline.cancel_event = cancel_event
    pipeline._completed_media = 0
    pipeline._total_media_hint = 0

    with pytest.raises(PipelineCancelled):
        pipeline._check_cancelled()

    assert events[-1]["stage"] == "cancelled"


def test_emit_contains_stage_progress():
    events = []
    pipeline = object.__new__(ControllableMediaPipeline)
    pipeline.event_callback = events.append
    pipeline._completed_media = 2
    pipeline._total_media_hint = 5
    pipeline._emit("transcribing", "Transcribing video", percent=35, file="video.mp4")

    assert events == [
        {
            "stage": "transcribing",
            "message": "Transcribing video",
            "completed": 2,
            "total": 5,
            "percent": 35,
            "file": "video.mp4",
        }
    ]
