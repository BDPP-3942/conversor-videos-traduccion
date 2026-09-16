from __future__ import annotations

import json
import logging
import os
import tempfile
import wave
from pathlib import Path
from typing import Any

from config.settings import BASE_DIR, AppSettings
from src.media_converter import MediaConverter

logger = logging.getLogger(__name__)
DEFAULT_MODEL_DIR = BASE_DIR / "tools" / "models" / "stt" / "vosk-model-small-es-0.42"


class VoskSTTEngine:
    """Motor STT ligero para Windows x86 basado en Vosk."""

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.model = self._load_model()
        self.converter = MediaConverter(settings)

    @staticmethod
    def _model_path() -> Path:
        configured = os.getenv("VOSK_MODEL_DIR", "").strip()
        return Path(configured).expanduser() if configured else DEFAULT_MODEL_DIR

    def _load_model(self) -> Any:
        model_path = self._model_path()
        if not model_path.is_dir():
            raise RuntimeError(
                "No se ha encontrado el modelo Vosk para Windows x86. "
                f"Coloca el modelo en {model_path} o configura VOSK_MODEL_DIR."
            )
        try:
            from vosk import Model
        except ImportError as exc:
            raise RuntimeError("El motor STT x86 requiere la dependencia vosk==0.3.42.") from exc
        logger.info("Cargando modelo Vosk desde %s", model_path)
        return Model(str(model_path))

    def transcribe(self, media_path: Path) -> list[dict[str, Any]]:
        try:
            from vosk import KaldiRecognizer
        except ImportError as exc:
            raise RuntimeError("El motor STT x86 requiere la dependencia vosk==0.3.42.") from exc

        with tempfile.TemporaryDirectory(prefix="video-translation-stt-") as temp_dir:
            wav_path = Path(temp_dir) / "audio.wav"
            self.converter.extract_wav(media_path, wav_path)
            with wave.open(str(wav_path), "rb") as audio:
                if audio.getnchannels() != 1 or audio.getframerate() != 16000 or audio.getsampwidth() != 2:
                    raise RuntimeError("El audio PCM generado para Vosk no tiene el formato esperado")
                recognizer = KaldiRecognizer(self.model, audio.getframerate())
                recognizer.SetWords(True)
                words: list[dict[str, Any]] = []
                while data := audio.readframes(4000):
                    if recognizer.AcceptWaveform(data):
                        words.extend(self._result_words(recognizer.Result()))
                words.extend(self._result_words(recognizer.FinalResult()))

        return self._build_segments(words)

    @staticmethod
    def _result_words(payload: str) -> list[dict[str, Any]]:
        try:
            value = json.loads(payload)
        except json.JSONDecodeError:
            logger.warning("Vosk devolvió un resultado JSON no válido")
            return []
        result = value.get("result", [])
        return [word for word in result if isinstance(word, dict) and word.get("word")]

    def _build_segments(self, words: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not words:
            return []
        threshold = max(0.1, self.settings.whisper_subtitle_split_silence_duration_ms / 1000.0)
        segments: list[dict[str, Any]] = []
        current: list[dict[str, Any]] = []
        previous_end: float | None = None
        for word in words:
            start = float(word.get("start", 0.0))
            end = float(word.get("end", start))
            text = str(word.get("word", "")).strip()
            if not text or end <= start:
                continue
            if current and previous_end is not None and start - previous_end > threshold:
                segments.append(self._segment(current))
                current = []
            current.append({"start": start, "end": end, "word": text})
            previous_end = end
        if current:
            segments.append(self._segment(current))
        return [segment for segment in segments if segment["text"]]

    @staticmethod
    def _segment(words: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "start": float(words[0]["start"]),
            "end": float(words[-1]["end"]),
            "text": " ".join(str(word["word"]) for word in words),
        }
