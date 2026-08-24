from __future__ import annotations

import logging
import os
from pathlib import Path

from config.settings import AppSettings

logger = logging.getLogger(__name__)


class STTEngine:
    def __init__(self, settings: AppSettings) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("STT support requires the faster-whisper package") from exc
        self.settings = settings
        threads = settings.whisper_cpu_threads
        if threads <= 0:
            threads = max(1, (os.cpu_count() or 4) // max(1, settings.max_parallel_videos))
        self.model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            cpu_threads=threads,
            num_workers=1,
        )
        logger.info(
            "Whisper ready: model=%s device=%s compute=%s cpu_threads=%d beam=%d vad=%s condition_previous=%s",
            settings.whisper_model,
            settings.whisper_device,
            settings.whisper_compute_type,
            threads,
            settings.whisper_beam_size,
            settings.whisper_vad_filter,
            settings.whisper_condition_on_previous_text,
        )

    def transcribe(self, media_path: Path):
        logger.info("Transcribing: %s", media_path.name)
        segments, _ = self.model.transcribe(
            str(media_path),
            language=self.settings.source_lang,
            task="transcribe",
            beam_size=max(1, self.settings.whisper_beam_size),
            best_of=1,
            temperature=0,
            condition_on_previous_text=self.settings.whisper_condition_on_previous_text,
            vad_filter=self.settings.whisper_vad_filter,
            vad_parameters={"min_silence_duration_ms": 2000} if self.settings.whisper_vad_filter else None,
            word_timestamps=False,
        )
        result = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                result.append({"start": float(segment.start), "end": float(segment.end), "text": text})
        logger.info("STT completed: %d segments", len(result))
        return result
