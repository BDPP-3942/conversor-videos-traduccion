from __future__ import annotations

import logging
from pathlib import Path

import webvtt

logger = logging.getLogger(__name__)


class VTTBuilder:
    @staticmethod
    def _format_time(seconds: float) -> str:
        if seconds < 0:
            raise ValueError("Subtitle time cannot be negative")
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    @classmethod
    def validate_segments(cls, segments: list[dict]) -> None:
        previous_end = 0.0
        for index, segment in enumerate(segments, start=1):
            start = float(segment["start"])
            end = float(segment["end"])
            text = str(segment.get("text") or "").strip()
            if start < 0:
                raise ValueError(f"Segment {index}: start cannot be negative")
            if end <= start:
                raise ValueError(f"Segment {index}: end must be greater than start")
            if start < previous_end:
                logger.warning("Segment %d overlaps previous segment", index)
            if not text:
                logger.warning("Segment %d contains empty text", index)
            previous_end = max(previous_end, end)

    @classmethod
    def generate_vtt(cls, segments: list[dict], output_path: Path) -> None:
        cls.validate_segments(segments)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        vtt = webvtt.WebVTT()
        for segment in segments:
            vtt.captions.append(
                webvtt.Caption(
                    cls._format_time(segment["start"]),
                    cls._format_time(segment["end"]),
                    segment["text"],
                )
            )
        vtt.save(str(output_path))
