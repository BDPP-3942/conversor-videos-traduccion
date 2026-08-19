from __future__ import annotations
import logging
from typing import Any
from config.settings import AppSettings

logger = logging.getLogger(__name__)
0
class STTEngine:
    def __init__(self, settings: AppSettings) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("STT support requires the faster-whisper package") from exc
        self.settings = settings
        self.model = WhisperModel(
            settings.whisper_model,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )

    def transcribe(self, media_path):
        logger.info("Transcribing: %s", media_path.name)
        segments, _ = self.model.transcribe(
            str(media_path),
            language=self.settings.source_lang,
            beam_size=self.settings.whisper_beam_size,
            vad_filter=self.settings.whisper_vad_filter,
        )
        result = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                result.append(
                    {"start": float(segment.start), "end": float(segment.end), "text": text}
                )
        logger.info("STT completed: %d segments", len(result))
        return result
