import logging
from pathlib import Path
from typing import List, Dict, Any

import webvtt


logger = logging.getLogger(__name__)


class VTTBuilder:
    """
    Generador y validador de subtítulos WebVTT.
    """

    # ========================================================
    # FORMATO DE TIEMPO
    # ========================================================

    @staticmethod
    def _format_time(
        seconds: float,
    ) -> str:

        if seconds < 0:
            raise ValueError(
                "Subtitle time cannot be negative"
            )

        hours = int(
            seconds // 3600
        )

        minutes = int(
            (seconds % 3600) // 60
        )

        secs = seconds % 60

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:06.3f}"
        )

    # ========================================================
    # VALIDACIÓN
    # ========================================================

    @classmethod
    def validate_segments(
        cls,
        segments: List[Dict[str, Any]],
    ) -> None:

        previous_end = 0.0

        for index, segment in enumerate(
            segments,
            start=1,
        ):

            start = float(
                segment["start"]
            )

            end = float(
                segment["end"]
            )

            text = (
                segment.get("text")
                or ""
            ).strip()

            if start < 0:
                raise ValueError(
                    f"Segment {index}: "
                    "start cannot be negative"
                )

            if end <= start:
                raise ValueError(
                    f"Segment {index}: "
                    "end must be greater "
                    "than start"
                )

            if start < previous_end:
                logger.warning(
                    "Segment %d overlaps previous "
                    "segment",
                    index,
                )

            if not text:
                logger.warning(
                    "Segment %d contains empty text",
                    index,
                )

            previous_end = max(
                previous_end,
                end,
            )

    # ========================================================
    # GENERAR
    # ========================================================

    @classmethod
    def generate_vtt(
        cls,
        segments: List[Dict[str, Any]],
        output_path: Path,
    ) -> None:

        cls.validate_segments(
            segments
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        vtt = webvtt.WebVTT()

        for segment in segments:

            caption = webvtt.Caption(
                cls._format_time(
                    segment["start"]
                ),
                cls._format_time(
                    segment["end"]
                ),
                segment["text"],
            )

            vtt.captions.append(
                caption
            )

        vtt.save(
            str(output_path)
        )

        logger.info(
            "VTT saved: %s",
            output_path,
        )