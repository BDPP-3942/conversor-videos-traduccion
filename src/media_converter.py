from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from config.settings import AppSettings

logger = logging.getLogger(__name__)
MEDIA_EXTENSIONS = {".mp4", ".mp3", ".wmv", ".mov", ".mkv", ".avi"}


@dataclass(frozen=True)
class MediaArtifacts:
    mp4_path: Path
    mp3_path: Path


class MediaConverter:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.ffmpeg_bin = settings.ffmpeg_bin
        self.ffprobe_bin = settings.ffprobe_bin

    def convert(self, source: Path, output_stem: str, output_dir: Path) -> MediaArtifacts:
        if not source.is_file():
            raise FileNotFoundError(f"Media source does not exist: {source}")
        if source.suffix.lower() not in MEDIA_EXTENSIONS:
            raise ValueError(f"Unsupported media extension: {source.suffix}")

        output_dir.mkdir(parents=True, exist_ok=True)
        mp4 = output_dir / f"{output_stem}.mp4"
        mp3 = output_dir / f"{output_stem}.mp3"
        self._run(self._build_mp4_command(source, mp4))
        if self._has_audio(source):
            self._run(self._build_mp3_command(source, mp3))
        else:
            self._run(self._build_silent_mp3_command(source, mp3))
        for output in (mp4, mp3):
            if not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError(f"FFmpeg did not create a valid output: {output}")
        return MediaArtifacts(mp4, mp3)

    def _build_mp4_command(self, source: Path, output: Path) -> list[str]:
        if source.suffix.lower() == ".mp3":
            return [
                self.ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=1280x720:r=1",
                "-i", str(source), "-map", "0:v:0", "-map", "1:a:0", "-shortest",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                str(output),
            ]
        return [
            self.ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
            "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264",
            "-preset", self.settings.ffmpeg_preset, "-crf", str(self.settings.ffmpeg_crf),
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", self.settings.ffmpeg_audio_bitrate,
            "-movflags", "+faststart", str(output),
        ]

    def _build_mp3_command(self, source: Path, output: Path) -> list[str]:
        return [
            self.ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
            "-map", "0:a:0", "-vn", "-codec:a", "libmp3lame",
            "-q:a", str(self.settings.ffmpeg_mp3_quality), str(output),
        ]

    def _build_silent_mp3_command(self, source: Path, output: Path) -> list[str]:
        duration = self._get_duration_seconds(source)
        return [
            self.ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", f"{duration:.3f}", "-codec:a", "libmp3lame",
            "-q:a", str(self.settings.ffmpeg_mp3_quality), str(output),
        ]

    def _has_audio(self, source: Path) -> bool:
        result = self._run_probe([
            self.ffprobe_bin, "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=index", "-of", "csv=p=0", str(source),
        ])
        return bool(result.strip())

    def _get_duration_seconds(self, source: Path) -> float:
        output = self._run_probe([
            self.ffprobe_bin, "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(source),
        ])
        try:
            duration = float(output.strip())
        except ValueError as exc:
            raise RuntimeError("Could not determine media duration") from exc
        if duration <= 0:
            raise RuntimeError("Media duration must be positive")
        return duration

    def _run_probe(self, command: list[str]) -> str:
        try:
            result = subprocess.run(
                command, check=True, capture_output=True, text=True, timeout=60
            )
        except FileNotFoundError as exc:
            raise RuntimeError("ffprobe is not installed or not available in PATH") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("ffprobe timed out") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError((exc.stderr or "ffprobe failed").strip()) from exc
        return result.stdout

    def _run(self, command: list[str]) -> None:
        logger.debug("Running FFmpeg: %s", " ".join(command))
        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.settings.ffmpeg_timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("FFmpeg is not installed or not available in PATH") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("FFmpeg conversion timed out") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError((exc.stderr or "FFmpeg conversion failed").strip()) from exc
