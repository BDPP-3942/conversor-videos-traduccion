from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from config.settings import AppSettings
from src.ffmpeg_resolver import FFmpegResolver

logger = logging.getLogger(__name__)
MEDIA_EXTENSIONS = {".mp4", ".mp3", ".wmv", ".mov", ".mkv", ".avi"}


@dataclass(frozen=True)
class MediaArtifacts:
    mp4_path: Path
    mp3_path: Path


class MediaConverter:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.ffmpeg_bin = str(FFmpegResolver.resolve(settings))

    def convert(self, source: Path, output_stem: str, output_dir: Path) -> MediaArtifacts:
        if not source.is_file():
            raise FileNotFoundError(f"Media source does not exist: {source}")
        if source.suffix.lower() not in MEDIA_EXTENSIONS:
            raise ValueError(f"Unsupported media extension: {source.suffix}")

        output_dir.mkdir(parents=True, exist_ok=True)
        mp4 = output_dir / f"{output_stem}.mp4"
        mp3 = output_dir / f"{output_stem}.mp3"

        if source.suffix.lower() != ".mp3":
            self._ensure_audio_stream(source)
        self._run(self._build_mp4_command(source, mp4))
        self._run(self._build_mp3_command(source, mp3))

        for output in (mp4, mp3):
            if not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError(f"FFmpeg did not create a valid output: {output}")
        return MediaArtifacts(mp4, mp3)

    def _build_mp4_command(self, source: Path, output: Path) -> list[str]:
        if source.suffix.lower() == ".mp3":
            return [
                self.ffmpeg_bin,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=1280x720:r=1",
                "-i",
                str(source),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-shortest",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                str(output),
            ]
        return [
            self.ffmpeg_bin,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-c:v",
            "libx264",
            "-preset",
            self.settings.ffmpeg_preset,
            "-crf",
            str(self.settings.ffmpeg_crf),
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            self.settings.ffmpeg_audio_bitrate,
            "-movflags",
            "+faststart",
            str(output),
        ]

    def _build_mp3_command(self, source: Path, output: Path) -> list[str]:
        return [
            self.ffmpeg_bin,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            str(self.settings.ffmpeg_mp3_quality),
            str(output),
        ]

    def _ensure_audio_stream(self, source: Path) -> None:
        command = [
            self.ffmpeg_bin,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-frames:a",
            "1",
            "-f",
            "null",
            "-",
        ]
        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("FFmpeg no está disponible para procesar el medio") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("La comprobación de la pista de audio agotó el tiempo") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "").strip()
            raise RuntimeError(
                f"El medio no contiene una pista de audio procesable: {detail}"
            ) from exc

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
            raise RuntimeError(
                "FFmpeg no está disponible. Ejecuta `pip install -r requirements.txt` "
                "o configura FFMPEG_BIN."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("FFmpeg conversion timed out") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError((exc.stderr or "FFmpeg conversion failed").strip()) from exc
