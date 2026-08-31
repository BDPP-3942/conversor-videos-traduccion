from __future__ import annotations

import gc
import logging
import math
from pathlib import Path
from typing import Any

from config.settings import AppSettings

logger = logging.getLogger(__name__)


class STTEngine:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.device = settings.whisper_device
        self.compute_type = settings.whisper_compute_type
        self.model = self._load_model(self.device, self.compute_type)
        logger.info(
            "Whisper ready: profile=%s cpu=%d ram=%.1fGB available_ram=%.1fGB gpu=%s gpu_index=%d vram_free=%.1fGB "
            "model=%s device=%s compute=%s cpu_threads=%d beam=%d vad=%s",
            settings.resource_profile,
            settings.detected_logical_cpus,
            settings.detected_memory_gb,
            settings.detected_memory_available_gb,
            settings.detected_gpu_model or settings.detected_gpu_vendor,
            settings.detected_gpu_index,
            settings.detected_gpu_vram_gb,
            settings.whisper_model,
            self.device,
            self.compute_type,
            settings.whisper_cpu_threads if settings.whisper_cpu_threads > 0 else 4,
            settings.whisper_beam_size,
            settings.whisper_vad_filter,
        )

    def _load_model(self, device: str, compute_type: str):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("STT support requires the faster-whisper package") from exc
        threads = self.settings.whisper_cpu_threads if self.settings.whisper_cpu_threads > 0 else 4
        try:
            return WhisperModel(
                self.settings.whisper_model,
                device=device,
                compute_type=compute_type,
                cpu_threads=threads,
                num_workers=1,
            )
        except Exception as exc:
            if device != "cuda":
                raise
            # A CUDA failure is a capability/runtime failure, not a reason to retry
            # the same model repeatedly. Drop the failed object, collect Python refs,
            # and create exactly one CPU instance.
            logger.exception("Whisper CUDA initialization failed; falling back once to CPU")
            self.model = None
            gc.collect()
            cpu_compute = "int8"
            self.device = "cpu"
            self.compute_type = cpu_compute
            try:
                return WhisperModel(
                    self.settings.whisper_model,
                    device="cpu",
                    compute_type=cpu_compute,
                    cpu_threads=threads,
                    num_workers=1,
                )
            except Exception as cpu_exc:
                raise RuntimeError("Whisper failed on CUDA and controlled CPU fallback also failed") from cpu_exc

    @staticmethod
    def _valid_interval(start: float, end: float) -> bool:
        return math.isfinite(start) and math.isfinite(end) and start >= 0 and end > start

    def _split_segment_on_silence(self, segment: Any) -> list[dict[str, Any]]:
        words = list(getattr(segment, "words", None) or [])
        if not words:
            text = str(segment.text or "").strip()
            start = float(segment.start)
            end = float(segment.end)
            return [{"start": start, "end": end, "text": text}] if text and self._valid_interval(start, end) else []
        threshold = max(0.1, self.settings.whisper_min_silence_duration_ms / 1000.0)
        groups: list[list[Any]] = []
        current: list[Any] = []
        previous_end: float | None = None
        for word in words:
            start = float(word.start)
            end = float(word.end)
            if not self._valid_interval(start, end):
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
            if text and self._valid_interval(start, end):
                result.append({"start": start, "end": end, "text": text})
        return result

    def transcribe(self, media_path: Path):
        logger.info("Transcribing: %s using device=%s compute=%s", media_path.name, self.device, self.compute_type)
        vad_parameters = None
        if self.settings.whisper_vad_filter:
            vad_parameters = {"min_silence_duration_ms": max(100, self.settings.whisper_min_silence_duration_ms)}
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
        raw_count = split_count = discarded_count = 0
        for segment in segments:
            raw_count += 1
            split_segments = self._split_segment_on_silence(segment)
            if not split_segments:
                discarded_count += 1
            if len(split_segments) > 1:
                split_count += len(split_segments) - 1
            result.extend(split_segments)
        result.sort(key=lambda item: (float(item["start"]), float(item["end"])))
        logger.info("STT completed: %d subtitle segments from %d Whisper segments; split %d; discarded %d", len(result), raw_count, split_count, discarded_count)
        return result
