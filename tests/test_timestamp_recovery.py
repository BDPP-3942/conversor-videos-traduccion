from __future__ import annotations

import pytest

pytest.importorskip("webvtt")

from src.reprocessor import SubtitleReprocessor
from src.stt_engine import STTEngine


def test_stt_final_validation_removes_zero_duration_cues_and_keeps_valid_timeline():
    result = STTEngine._validate_final_segments([
        {"start": 2.0, "end": 1.0, "text": "invalid"},
        {"start": 0.0, "end": 1.0, "text": "hola"},
        {"start": 1.5, "end": 2.0, "text": "mundo"},
    ])
    assert result == [
        {"start": 0.0, "end": 1.0, "text": "hola"},
        {"start": 1.5, "end": 2.0, "text": "mundo"},
    ]


def test_stt_final_validation_rejects_remaining_overlaps():
    with pytest.raises(ValueError, match="overlapping timeline"):
        STTEngine._validate_final_segments([
            {"start": 0.0, "end": 2.0, "text": "uno"},
            {"start": 1.0, "end": 3.0, "text": "dos"},
        ])


def test_reprocessor_validation_rejects_start_equal_end():
    validation = SubtitleReprocessor._validate_segments([
        {"start": 1.0, "end": 1.0, "text": "zero"},
    ])
    assert validation["valid"] is False
    assert "invalid interval" in validation["errors"][0]
