from __future__ import annotations

import gc
import logging
import math
from pathlib import Path
from typing import Any

from config.settings import BASE_DIR, AppSettings
from src.cuda_runtime import ensure_cuda_runtime
from src.stt_quality import (
    STTQualityThresholds,
    candidate_key,
    quality_metrics,
    suspicious_reasons,
)
from src.whisper_prompt import resolve_initial_prompt

logger = logging.getLogger(__name__)


class STTEngine:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.device = settings.whisper_device
        self.compute_type = settings.whisper_compute_type
        self._quality_thresholds = STTQualityThresholds(
            repetition_threshold=settings.whisper_repetition_threshold,
            compression_ratio_threshold=settings.whisper_compression_ratio_threshold,
            log_prob_threshold=settings.whisper_log_prob_threshold,
            no_speech_threshold=settings.whisper_no_speech_threshold,
            min_repetition_words=settings.whisper_min_repetition_words,
        )
        if self.device in {"auto", "cuda"}:
            cuda_status = ensure_cuda_runtime(interactive=not getattr(settings, "unattended_mode", False))
            if self.device == "auto" and cuda_status.compatible:
                self.device = "cuda"
                self.compute_type = self.compute_type if self.compute_type != "auto" else "float16"
            elif self.device == "auto":
                self.device = "cpu"
                self.compute_type = self.compute_type if self.compute_type not in {"auto", "float16"} else "int8"
            elif self.device == "cuda" and not cuda_status.compatible:
                logger.warning(
                    "Whisper CUDA runtime is not ready; using CPU fallback: %s",
                    cuda_status.reason,
                )
                self.device = "cpu"
                self.compute_type = "int8"
        if self.compute_type == "auto":
            self.compute_type = "float16" if self.device == "cuda" else "int8"
        self.model = self._load_model(self.device, self.compute_type)
        logger.info(
            "Whisper ready: model=%s device=%s compute=%s beam=%d vad=%s context=%s",
            settings.whisper_model,
            self.device,
            self.compute_type,
            settings.whisper_beam_size,
            settings.whisper_vad_filter,
            settings.whisper_condition_on_previous_text,
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
        except Exception:
            if device != "cuda":
                raise
            logger.exception("Whisper CUDA initialization failed; falling back once to CPU")
            self.model = None
            gc.collect()
            self.device = "cpu"
            self.compute_type = "int8"
            return WhisperModel(
                self.settings.whisper_model,
                device="cpu",
                compute_type="int8",
                cpu_threads=threads,
                num_workers=1,
            )

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

    def _transcribe_kwargs(
        self,
        *,
        condition_on_previous_text: bool,
        temperature: float | tuple[float, ...],
        clip_timestamps: list[dict[str, float]] | None = None,
    ) -> dict[str, Any]:
        vad_parameters = None
        if self.settings.whisper_vad_filter and clip_timestamps is None:
            vad_parameters = {"min_silence_duration_ms": max(100, self.settings.whisper_min_silence_duration_ms)}
        kwargs: dict[str, Any] = {
            "language": self.settings.source_lang,
            "task": "transcribe",
            "beam_size": max(1, self.settings.whisper_beam_size),
            "best_of": 1,
            "temperature": temperature,
            "condition_on_previous_text": condition_on_previous_text,
            "vad_filter": self.settings.whisper_vad_filter if clip_timestamps is None else False,
            "vad_parameters": vad_parameters,
            "word_timestamps": True,
            "compression_ratio_threshold": self.settings.whisper_compression_ratio_threshold,
            "log_prob_threshold": self.settings.whisper_log_prob_threshold,
            "no_speech_threshold": self.settings.whisper_no_speech_threshold,
            "hallucination_silence_threshold": getattr(
                self.settings,
                "whisper_hallucination_silence_threshold",
                None,
            ),
        }
        if clip_timestamps is not None:
            kwargs["clip_timestamps"] = clip_timestamps
        prompt, prompt_source = resolve_initial_prompt(
            self.settings.whisper_initial_prompt,
            BASE_DIR,
        )
        if prompt:
            kwargs["initial_prompt"] = prompt
        logger.debug(
            "Whisper initial prompt source=%s length=%d",
            prompt_source,
            len(prompt),
        )
        return kwargs

    def _collect_segments(self, segments: Any) -> list[Any]:
        return list(segments)

    def _candidate_segments(self, media_path: Path, start: float, end: float) -> list[Any]:
        candidates: list[Any] = []
        temperatures = tuple(self.settings.whisper_recovery_temperatures)
        for temperature in temperatures:
            kwargs = self._transcribe_kwargs(
                condition_on_previous_text=True,
                temperature=temperature,
                clip_timestamps=[{"start": start, "end": end}],
            )
            candidates.extend(self._collect_segments(self.model.transcribe(str(media_path), **kwargs)[0]))
        if candidates and not all(self._is_suspicious(segment) for segment in candidates):
            return candidates

        kwargs = self._transcribe_kwargs(
            condition_on_previous_text=False,
            temperature=temperatures[-1] if temperatures else 0,
            clip_timestamps=[{"start": start, "end": end}],
        )
        candidates.extend(self._collect_segments(self.model.transcribe(str(media_path), **kwargs)[0]))
        return candidates

    def _is_suspicious(self, segment: Any) -> bool:
        return bool(suspicious_reasons(quality_metrics(segment), self._quality_thresholds))

    def _select_candidate(self, candidates: list[Any]) -> Any | None:
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda segment: candidate_key(segment, self._quality_thresholds),
        )

    def _recover_segment(self, media_path: Path, segment: Any) -> list[Any]:
        start = max(0.0, float(segment.start))
        end = max(start, float(segment.end))
        if end <= start:
            return []
        candidates = self._candidate_segments(media_path, start, end)
        selected = self._select_candidate(candidates)
        if selected is None:
            return []
        metrics = quality_metrics(selected)
        reasons = suspicious_reasons(metrics, self._quality_thresholds)
        logger.info(
            "STT recovery: start=%.3f end=%.3f candidates=%d "
            "selected_suspicious=%s reasons=%s repetition=%.3f "
            "compression=%s avg_logprob=%s no_speech=%s",
            start,
            end,
            len(candidates),
            bool(reasons),
            ",".join(reasons) or "none",
            metrics.repetition_score,
            metrics.compression_ratio,
            metrics.avg_logprob,
            metrics.no_speech_prob,
        )
        return [selected] if not reasons else []

    def transcribe(self, media_path: Path):
        logger.info(
            "Transcribing: %s using device=%s compute=%s",
            media_path.name,
            self.device,
            self.compute_type,
        )
        kwargs = self._transcribe_kwargs(
            condition_on_previous_text=self.settings.whisper_condition_on_previous_text,
            temperature=0,
        )
        segments = self._collect_segments(self.model.transcribe(str(media_path), **kwargs)[0])
        result: list[dict[str, Any]] = []
        recovered = 0
        suspicious = 0
        for segment in segments:
            if self._is_suspicious(segment):
                suspicious += 1
                recovered_segments = self._recover_segment(media_path, segment)
                if recovered_segments:
                    segments_to_emit = recovered_segments
                    recovered += 1
                else:
                    logger.warning(
                        "STT suspicious result rejected after recovery: start=%.3f end=%.3f",
                        float(segment.start),
                        float(segment.end),
                    )
                    continue
            else:
                segments_to_emit = [segment]
            for candidate in segments_to_emit:
                result.extend(self._split_segment_on_silence(candidate))
        result.sort(key=lambda item: (float(item["start"]), float(item["end"])))
        logger.info(
            "STT completed: %d subtitle segments; suspicious=%d recovered=%d",
            len(result),
            suspicious,
            recovered,
        )
        return result
