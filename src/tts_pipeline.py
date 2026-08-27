from __future__ import annotations

import logging
import re
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import webvtt

from config.settings import AppSettings, resolve_project_path

logger = logging.getLogger(__name__)


class TTSProvider(Protocol):
    """Minimal provider contract used by the synchronization layer."""

    def synthesize(self, text: str, *, language: str, voice: str, speed: float) -> tuple[object, int]:
        """Return mono PCM samples and their sample rate."""


class TTSProviderError(RuntimeError):
    """Raised when a TTS provider cannot synthesize a cue."""


@dataclass(frozen=True)
class TTSCue:
    start: float
    end: float
    text: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass(frozen=True)
class TTSResult:
    audio_path: Path
    mp4_path: Path
    webm_path: Path | None
    cue_count: int
    adjusted_cues: int


class KokoroONNXProvider:
    """Local Kokoro-82M provider loaded lazily so TTS stays optional."""

    def __init__(self, model_path: Path, voices_path: Path) -> None:
        self.model_path = model_path
        self.voices_path = voices_path
        self._engine = None

    def _load(self):
        if self._engine is not None:
            return self._engine
        try:
            from kokoro_onnx import Kokoro
        except ImportError as exc:
            raise TTSProviderError(
                "Kokoro TTS is not installed. Install the optional TTS dependencies before enabling TTS."
            ) from exc
        if not self.model_path.is_file():
            raise TTSProviderError(f"Kokoro model not found: {self.model_path}")
        if not self.voices_path.is_file():
            raise TTSProviderError(f"Kokoro voices file not found: {self.voices_path}")
        self._engine = Kokoro(str(self.model_path), str(self.voices_path))
        return self._engine

    def synthesize(self, text: str, *, language: str, voice: str, speed: float) -> tuple[object, int]:
        engine = self._load()
        try:
            samples, sample_rate = engine.create(
                text,
                voice=voice,
                speed=speed,
                lang=_kokoro_language(language),
            )
        except Exception as exc:  # provider boundary: third-party exceptions are normalized
            raise TTSProviderError(f"Kokoro synthesis failed: {exc}") from exc
        return samples, int(sample_rate)


def create_tts_provider(settings: AppSettings) -> TTSProvider:
    provider = settings.tts_provider.lower()
    if provider != "kokoro":
        raise ValueError(f"Unsupported TTS provider: {settings.tts_provider}")
    return KokoroONNXProvider(
        resolve_project_path(settings.tts_model_path),
        resolve_project_path(settings.tts_voices_path),
    )


def generate_tts_media(
    video_path: Path,
    translated_vtt_path: Path,
    output_dir: Path,
    output_stem: str,
    settings: AppSettings,
    *,
    webm_video_path: Path | None = None,
    provider: TTSProvider | None = None,
) -> TTSResult:
    """Generate a timeline-aligned narration track and mux it into MP4/WebM."""
    if not video_path.is_file():
        raise FileNotFoundError(f"TTS video source does not exist: {video_path}")
    if not translated_vtt_path.is_file():
        raise FileNotFoundError(f"TTS VTT source does not exist: {translated_vtt_path}")

    cues = _read_cues(translated_vtt_path)
    if not cues:
        raise ValueError(f"Translated VTT contains no usable cues: {translated_vtt_path}")
    provider = provider or create_tts_provider(settings)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=f"{output_stem}_tts_", dir=output_dir) as tmp:
        temp_root = Path(tmp)
        audio_path = temp_root / f"{output_stem}_tts.wav"
        adjusted_cues = _render_timeline(cues, provider, settings, audio_path)
        mp4_path = output_dir / f"{output_stem}_tts.mp4"
        _mux_video(video_path, audio_path, mp4_path, settings, webm=False)
        _validate_media(mp4_path, settings, require_video=True, require_audio=True, expected_audio="aac")

        webm_path: Path | None = None
        if settings.tts_generate_webm and settings.generate_webm:
            webm_source = webm_video_path if webm_video_path and webm_video_path.is_file() else video_path
            webm_path = output_dir / f"{output_stem}_tts.webm"
            _mux_video(webm_source, audio_path, webm_path, settings, webm=True)
            _validate_media(webm_path, settings, require_video=True, require_audio=True, expected_audio="opus")

        final_audio = output_dir / f"{output_stem}_tts.wav"
        final_audio.write_bytes(audio_path.read_bytes())
        return TTSResult(final_audio, mp4_path, webm_path, len(cues), adjusted_cues)


def _read_cues(path: Path) -> list[TTSCue]:
    captions = webvtt.read(str(path))
    cues: list[TTSCue] = []
    previous_end = -1.0
    for index, caption in enumerate(captions, 1):
        start = _timestamp(caption.start)
        end = _timestamp(caption.end)
        if start < 0 or end <= start:
            raise ValueError(f"Invalid VTT timing at cue {index}: {caption.start} --> {caption.end}")
        if start < previous_end:
            raise ValueError(f"Overlapping VTT cues at cue {index}")
        text = re.sub(r"\s+", " ", caption.text.replace("\n", " ")).strip()
        cues.append(TTSCue(start, end, text))
        previous_end = end
    return cues


def _render_timeline(
    cues: list[TTSCue],
    provider: TTSProvider,
    settings: AppSettings,
    output: Path,
) -> int:
    import numpy as np

    sample_rate = int(settings.tts_sample_rate)
    timeline = np.zeros(1, dtype=np.float32)
    adjusted = 0
    for cue_index, cue in enumerate(cues, 1):
        target_samples = max(1, round(cue.duration * sample_rate))
        if not cue.text:
            continue
        speed = max(0.1, float(settings.tts_speed))
        samples, generated_rate = provider.synthesize(
            cue.text,
            language=settings.target_lang,
            voice=settings.tts_voice,
            speed=speed,
        )
        audio = _normalize_samples(samples)
        if generated_rate != sample_rate:
            audio = _resample_linear(audio, generated_rate, sample_rate)
        if len(audio) > target_samples * (1.0 + settings.tts_duration_tolerance):
            required_speed = speed * len(audio) / target_samples
            if required_speed <= settings.tts_max_speed:
                speed = min(settings.tts_max_speed, required_speed * 1.01)
                samples, generated_rate = provider.synthesize(
                    cue.text,
                    language=settings.target_lang,
                    voice=settings.tts_voice,
                    speed=speed,
                )
                audio = _normalize_samples(samples)
                if generated_rate != sample_rate:
                    audio = _resample_linear(audio, generated_rate, sample_rate)
                adjusted += 1
        if len(audio) > target_samples:
            if len(audio) > target_samples * (1.0 + settings.tts_duration_tolerance):
                raise TTSProviderError(
                    f"Cue {cue_index} cannot fit in {cue.duration:.3f}s at max TTS speed {settings.tts_max_speed:.2f}"
                )
            audio = audio[:target_samples]
        start_samples = round(cue.start * sample_rate)
        required_length = start_samples + len(audio)
        if required_length > len(timeline):
            timeline = np.pad(timeline, (0, required_length - len(timeline)))
        timeline[start_samples : start_samples + len(audio)] = audio

    if len(timeline) < 2:
        timeline = np.zeros(2, dtype=np.float32)
    _write_wav(output, np.clip(timeline, -1.0, 1.0), sample_rate)
    return adjusted


def _resolve_ffmpeg(settings: AppSettings) -> Path:
    from src.ffmpeg_resolver import FFmpegResolver

    configured = str(settings.ffmpeg_bin).strip()
    executable = Path(configured).expanduser() if configured else FFmpegResolver.resolve(settings)
    if not executable.is_absolute():
        executable = resolve_project_path(executable)
    executable = executable.resolve()
    if not executable.is_file():
        raise RuntimeError(f"FFmpeg executable not found: {executable}")
    return executable


def _mux_video(source: Path, audio: Path, output: Path, settings: AppSettings, *, webm: bool) -> None:
    ffmpeg = _resolve_ffmpeg(settings)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source.resolve()),
        "-i",
        str(audio.resolve()),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
    ]
    if webm and source.suffix.lower() == ".webm":
        command += ["-c:v", "copy", "-c:a", "libopus", "-b:a", settings.tts_webm_audio_bitrate]
    elif webm:
        command += [
            "-c:v",
            "libvpx-vp9",
            "-crf",
            "32",
            "-b:v",
            "0",
            "-c:a",
            "libopus",
            "-b:a",
            settings.tts_webm_audio_bitrate,
        ]
    else:
        command += [
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            settings.tts_audio_bitrate,
            "-movflags",
            "+faststart",
        ]
    command.append(str(output.resolve()))
    _run_ffmpeg(command, settings.ffmpeg_timeout_seconds)


def _validate_media(
    path: Path,
    settings: AppSettings,
    *,
    require_video: bool,
    require_audio: bool,
    expected_audio: str | None = None,
) -> None:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeError(f"Media artifact is missing or empty: {path}")
    ffmpeg = _resolve_ffmpeg(settings)
    command = [str(ffmpeg), "-hide_banner", "-i", str(path.resolve())]
    try:
        result = subprocess.run(  # noqa: S603 -- shell=False and only resolved local paths/constants are used
            command,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            shell=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"Could not validate media artifact: {path}") from exc
    stderr = result.stderr or ""
    if result.returncode != 0 and "Duration:" not in stderr:
        raise RuntimeError(f"Invalid media container: {path}")
    if require_video and not re.search(r"Stream #\d+:\d+.*Video:", stderr):
        raise RuntimeError(f"TTS artifact has no video stream: {path}")
    if require_audio and not re.search(r"Stream #\d+:\d+.*Audio:", stderr):
        raise RuntimeError(f"TTS artifact has no audio stream: {path}")
    if expected_audio and not re.search(rf"Audio:\s*{re.escape(expected_audio)}\b", stderr, re.IGNORECASE):
        raise RuntimeError(f"TTS artifact does not contain expected audio codec {expected_audio}: {path}")


def _run_ffmpeg(command: list[str], timeout: int) -> None:
    logger.debug("Running TTS FFmpeg command: %s", " ".join(command))
    try:
        result = subprocess.run(  # noqa: S603 -- shell=False; executable and argv are generated internally
            command,
            capture_output=True,
            text=True,
            timeout=max(30, timeout),
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("TTS FFmpeg operation timed out") from exc
    if result.returncode != 0:
        detail = (result.stderr or "FFmpeg failed").strip().splitlines()[-1]
        raise RuntimeError(detail)


def _normalize_samples(samples: object):
    import numpy as np

    array = np.asarray(samples, dtype=np.float32).reshape(-1)
    if array.size == 0:
        raise TTSProviderError("TTS provider returned empty audio")
    peak = float(np.max(np.abs(array)))
    return array / peak if peak > 1.0 else array


def _resample_linear(samples, source_rate: int, target_rate: int):
    import numpy as np

    if source_rate == target_rate or len(samples) < 2:
        return samples
    target_length = max(1, round(len(samples) * target_rate / source_rate))
    source_positions = np.linspace(0, len(samples) - 1, target_length)
    return np.interp(source_positions, np.arange(len(samples)), samples).astype(np.float32)


def _write_wav(path: Path, samples, sample_rate: int) -> None:
    import numpy as np

    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def _timestamp(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
    elif len(parts) == 2:
        hours = "0"
        minutes, seconds = parts
    else:
        raise ValueError(f"Invalid VTT timestamp: {value}")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _kokoro_language(language: str) -> str:
    normalized = language.lower().replace("_", "-")
    return {
        "en": "en-us",
        "en-us": "en-us",
        "en-gb": "en-gb",
        "es": "es",
        "es-es": "es",
        "fr": "fr-fr",
        "it": "it",
        "pt": "pt-br",
        "pt-br": "pt-br",
        "ja": "ja",
        "zh": "zh",
        "hi": "hi",
    }.get(normalized, normalized)
