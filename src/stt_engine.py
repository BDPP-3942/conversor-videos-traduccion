from pathlib import Path
from typing import List, Dict, Any
from faster_whisper import WhisperModel
from config import settings

class STTEngine:
    def __init__(self):
        print(f"[STT] Initializing Whisper model '{settings.WHISPER_MODEL}' on CPU ({settings.WHISPER_COMPUTE_TYPE})...")
        self.model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE_TYPE
        )

    def transcribe(self, video_path: Path) -> List[Dict[str, Any]]:
        print(f"[STT] Transcribing: {video_path.name}")
        segments, info = self.model.transcribe(
            str(video_path),
            language=settings.SOURCE_LANG,
            beam_size=5,
            vad_filter=True
        )
        
        result_segments = []
        for segment in segments:
            result_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
        print(f"[STT] Done: {len(result_segments)} segments generated.")
        return result_segments
