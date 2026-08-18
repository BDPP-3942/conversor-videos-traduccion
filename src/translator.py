import logging
from typing import List, Dict, Any

from deep_translator import GoogleTranslator

from config import settings


logger = logging.getLogger(__name__)


class TextTranslator:
    """
    Traduce los segmentos generados por el STT.
    """

    def __init__(self):

        self.translator = GoogleTranslator(
            source=settings.SOURCE_LANG,
            target=settings.TARGET_LANG,
        )

    def translate_segments(
        self,
        segments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        logger.info(
            "Translating %d segments "
            "(%s -> %s)",
            len(segments),
            settings.SOURCE_LANG,
            settings.TARGET_LANG,
        )

        translated_segments = []

        for index, segment in enumerate(
            segments,
            start=1,
        ):

            text = segment["text"].strip()

            if not text:
                translated_text = ""

            else:
                try:
                    translated_text = (
                        self.translator.translate(
                            text
                        )
                    )

                except Exception as exc:
                    raise RuntimeError(
                        "Translation failed for "
                        f"segment {index}: {exc}"
                    ) from exc

            translated_segments.append(
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": (
                        translated_text or ""
                    ).strip(),
                }
            )

        logger.info(
            "Translation completed"
        )

        return translated_segments