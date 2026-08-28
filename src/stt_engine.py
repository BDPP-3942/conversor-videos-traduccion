from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from config.settings import AppSettings

logger = logging.getLogger(__name__)
TIMESTAMP_EPSILON = 0.001


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

    def _split_segment_on_silence(self, segment: Any) -> list[dict[str, Any]]:
        """Split one Whisper segment when word timestamps contain a real pause."""
        words = list(getattr(segment, "words", None) or [])
        if not words:
            text = str(segment.text or "").strip()
            if not text:
                return []
            start = float(segment.start)
            end = float(segment.end)
            return [{"start": start, "end": end, "text": text}] if end > start else []

        threshold = max(0.1, self.settings.whisper_min_silence_duration_ms / 1000.0)
        groups: list[list[Any]] = []
        current: list[Any] = []
        previous_end: float | None = None
        for word in words:
            start = float(word.start)
            end = float(word.end)
            if end <= start:
                continue
            if current and previous_end is not None and start - previous_end >= threshold:
                groups.append(current)
                current = []
            current.append(word)
            previous_end = end
        if current:
            groups.append(current)

        result: list[dict[str, Any]] = []
        for group in groups:
            text = "".join(str(word.word or "") for word in group).strip()
            start = float(group[0].start)
            end = float(group[-1].end)
            if text and end > start:
                result.append({"start": start, "end": end, "text": text})
        return result

    @staticmethod
    def _validate_final_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return only usable cues and fail if the resulting timeline is inconsistent."""
        cleaned: list[dict[str, Any]] = []
        for index, segment in enumerate(segments, 1):
            try:
                start = float(segment["start"])
                end = float(segment["end"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"STT segment {index} has non-numeric timestamps") from exc
            if start < 0 or end <= start:
                logger.warning("Discarding invalid STT segment %d: %.3f --> %.3f", index, start, end)
                continue
            text = str(segment.get("text", "")).strip()
            if not text:
                continue
            cleaned.append({"start": start, "end": end, "text": text})

        cleaned.sort(key=lambda item: (item["start"], item["end"]))
        previous_end = -1.0
        for index, segment in enumerate(cleaned, 1):
            if segment["start"] + TIMESTAMP_EPSILON < previous_end:
                raise ValueError(
                    f"STT produced overlapping timeline at segment {index}: "
                    f"{segment['start']:.3f} < previous end {previous_end:.3f}"
                )
            previous_end = segment["end"]
        if not cleaned:
            raise ValueError("STT produced no valid subtitle segments")
        return cleaned

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
            "word_timestamps": True,
        }
        prompt = self.settings.whisper_initial_prompt.strip()
        if prompt:
            transcribe_kwargs["initial_prompt"] = prompt
        segments, _ = self.model.transcribe(str(media_path), **transcribe_kwargs)
        result: list[dict[str, Any]] = []
        raw_count = 0
        split_count = 0
        for segment in segments:
            raw_count += 1
            split_segments = self._split_segment_on_silence(segment)
            if len(split_segments) > 1:
                split_count += len(split_segments) - 1
            result.extend(split_segments)

        result = self._validate_final_segments(result)
        logger.info(
            "STT completed: %d subtitle segments from %d Whisper segments; split %d internal silence gaps",
            len(result),
            raw_count,
            split_count,
        )
        return result
