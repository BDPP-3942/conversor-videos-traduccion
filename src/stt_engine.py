import logging
from pathlib import Path
from typing import List, Dict, Any

from faster_whisper import WhisperModel

from config import settings


logger = logging.getLogger(__name__)


class STTEngine:
    """
    Motor Speech-To-Text basado en faster-whisper.
    """

    def __init__(self):

        logger.info(
            "Initializing Whisper model '%s' "
            "on %s (%s)",
            settings.WHISPER_MODEL,
            settings.WHISPER_DEVICE,
            settings.WHISPER_COMPUTE_TYPE,
        )

        self.model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=(
                settings.WHISPER_COMPUTE_TYPE
            ),
        )

    def transcribe(
        self,
        video_path: Path,
    ) -> List[Dict[str, Any]]:

        logger.info(
            "Transcribing: %s",
            video_path.name,
        )

        segments, _ = self.model.transcribe(
            str(video_path),
            language=settings.SOURCE_LANG,
            beam_size=settings.WHISPER_BEAM_SIZE,
            vad_filter=settings.WHISPER_VAD_FILTER,
        )

        result_segments = []

        for segment in segments:

            text = segment.text.strip()

            if not text:
                continue

            result_segments.append(
                {
                    "start": float(
                        segment.start
                    ),
                    "end": float(
                        segment.end
                    ),
                    "text": text,
                }
            )

        logger.info(
            "STT completed: %d segments",
            len(result_segments),
        )

        return result_segments
    