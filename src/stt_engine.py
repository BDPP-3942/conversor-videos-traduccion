from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from config.settings import AppSettings

logger = logging.getLogger(__name__)


class STTEngine:
    def __init__(self, settings: AppSettings) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("STT support requires the faster-whisper package") from exc

        self.settings = settings
        threads = settings.whisper_cpu_threads if settings.whisper_cpu_threads > 0 else 4
        self.model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            cpu_threads=threads,
            num_workers=1,
        )
        logger.info(
            "Whisper ready: profile=%s cpu=%d ram=%.1fGB model=%s device=%s "
            "compute=%s cpu_threads=%d beam=%d vad=%s min_silence_ms=%d "
            "condition_previous=%s prompt=%s",
            settings.resource_profile,
            settings.detected_logical_cpus,
            settings.detected_memory_gb,
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type,
            threads,
            settings.whisper_beam_size,
            settings.whisper_vad_filter,
            settings.whisper_min_silence_duration_ms,
            settings.whisper_condition_on_previous_text,
            bool(settings.whisper_initial_prompt.strip()),
        )

    @staticmethod
    def _segment_from_whisper(segment: Any) -> dict[str, Any]:
        return {
            "start": max(0.0, float(segment.start)),
            "end": max(0.0, float(segment.end)),
            "text": str(segment.text or "").strip(),
        }

    @classmethod
    def _preserve_silence_boundaries(cls, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Keep each cue inside the voiced region reported by Whisper.

        Whisper's segment boundaries may span a long pause even when VAD detects
        that the middle of the segment is silent.  A segment must therefore not
        be allowed to carry its subtitle across a later segment's start.  The
        next non-empty segment is the authoritative boundary for the preceding
        cue, while its own start remains the beginning of the next spoken cue.
        """
        result: list[dict[str, Any]] = []
        for index, segment in enumerate(segments):
            start = float(segment["start"])
            end = float(segment["end"])
            if index + 1 < len(segments):
                next_start = float(segments[index + 1]["start"])
                if next_start > start and next_start < end:
                    end = next_start
            if end <= start:
                logger.warning(
                    "Discarding invalid STT cue after silence-boundary correction: %.3f -> %.3f",
                    start,
                    end,
                )
                continue
            result.append({**segment, "start": start, "end": end})
        return result

    def transcribe(self, media_path: Path):
        logger.info("Transcribing: %s", media_path.name)
        vad_parameters = None
        if self.settings.whisper_vad_filter:
            vad_parameters = {
                "min_silence_duration_ms": max(100, self.settings.whisper_min_silence_duration_ms),
            }
        transcribe_kwargs = {
            "language": self.settings.source_lang,
            "task": "transcribe",
            "beam_size": max(1, self.settings.whisper_beam_size),
            "best_of": 1,
            "temperature": 0,
            "condition_on_previous_text": self.settings.whisper_condition_on_previous_text,
            "vad_filter": self.settings.whisper_vad_filter,
            "vad_parameters": vad_parameters,
            "word_timestamps": False,
        }
        prompt = self.settings.whisper_initial_prompt.strip()
        if prompt:
            transcribe_kwargs["initial_prompt"] = prompt
        segments, _ = self.model.transcribe(str(media_path), **transcribe_kwargs)
        raw_segments = [self._segment_from_whisper(segment) for segment in segments]
        non_empty = [segment for segment in raw_segments if segment["text"]]
        result = self._preserve_silence_boundaries(non_empty)
        logger.info(
            "STT completed: %d segments (%d raw non-empty); subtitle gaps are preserved",
            len(result),
            len(non_empty),
        )
        return result
