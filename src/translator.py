from typing import List, Dict, Any
from deep_translator import GoogleTranslator
from config import settings

class TextTranslator:
    def __init__(self):
        self.translator = GoogleTranslator(
            source=settings.SOURCE_LANG,
            target=settings.TARGET_LANG
        )

    def translate_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        print(f"[TRANSLATE] Translating {len(segments)} segments ({settings.SOURCE_LANG} -> {settings.TARGET_LANG})...")
        translated_segments = []
        for seg in segments:
            translated_text = self.translator.translate(seg["text"]) if seg["text"] else ""
            translated_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": translated_text
            })
        print("[TRANSLATE] Translation finished.")
        return translated_segments
