from pathlib import Path
from typing import List, Dict, Any
import webvtt

class VTTBuilder:
    @staticmethod
    def _format_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    @classmethod
    def generate_vtt(cls, segments: List[Dict[str, Any]], output_path: Path):
        vtt = webvtt.WebVTT()
        for seg in segments:
            caption = webvtt.Caption(
                cls._format_time(seg["start"]),
                cls._format_time(seg["end"]),
                seg["text"]
            )
            vtt.captions.append(caption)
        vtt.save(str(output_path))
        print(f"[VTT] Subtitle saved to: {output_path.name}")
