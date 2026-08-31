from __future__ import annotations

import logging
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from config.settings import AppSettings
from src.ffmpeg_resolver import FFmpegResolver

logger = logging.getLogger(__name__)
MEDIA_EXTENSIONS = {".mp3", ".mp4", ".wmv", ".mov", ".mkv", ".avi", ".webm", ".m4v"}

@dataclass(frozen=True)
class MediaArtifacts:
    mp4_path: Path
    secondary_video_path: Path | None

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
        secondary: Path | None = None
        if self.settings.generate_webm:
            extension = self.settings.secondary_video_extension.lower().lstrip(".")
            secondary = output_dir / f"{output_stem}.{extension}"
        if source.suffix.lower() == ".mp4" and self.settings.ffmpeg_avoid_reencode:
            try:
                self._run(self._build_mp4_copy_command(source, mp4))
            except RuntimeError:
                logger.info("MP4 copy path failed; falling back to H.264/AAC transcode: %s", source.name)
                self._run(self._build_mp4_command(source, mp4))
        else:
            self._run(self._build_mp4_command(source, mp4))
        if secondary is not None:
            self._run(self._build_secondary_video_command(source, secondary))
        for output in (mp4, secondary):
            if output is not None and (not output.is_file() or output.stat().st_size == 0):
                raise RuntimeError(f"FFmpeg did not create a valid output: {output}")
        return MediaArtifacts(mp4, secondary)

    def _build_mp4_copy_command(self, source: Path, output: Path) -> list[str]:
        return [self.ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", "-movflags", "+faststart", str(output)]

    def _build_mp4_command(self, source: Path, output: Path) -> list[str]:
        if source.suffix.lower() == ".mp3":
            return [self.ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=1280x720:r=1", "-i", str(source), "-map", "0:v:0", "-map", "1:a:0", "-shortest", "-c:v", "libx264", "-preset", self.settings.ffmpeg_preset, "-crf", str(self.settings.ffmpeg_crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", self.settings.ffmpeg_audio_bitrate, str(output)]
        return [self.ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-map", "0:v:0", "-map", "0:a:0?", "-c:v", "libx264", "-preset", self.settings.ffmpeg_preset, "-crf", str(self.settings.ffmpeg_crf), "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", self.settings.ffmpeg_audio_bitrate, "-movflags", "+faststart", str(output)]

    def _build_secondary_video_command(self, source: Path, output: Path) -> list[str]:
        codec = self.settings.secondary_video_codec
        max_width = int(self.settings.secondary_video_max_width)
        fps = int(self.settings.secondary_video_fps)
        command = [self.ffmpeg_bin, "-hide_banner", "-loglevel", "error", "-y"]
        if source.suffix.lower() == ".mp3":
            video_width = max_width if max_width > 0 else 1280
            video_fps = fps if fps > 0 else 24
            command += ["-f", "lavfi", "-i", f"color=c=black:s={video_width}x720:r={video_fps}", "-i", str(source), "-map", "0:v:0", "-map", "1:a:0", "-shortest"]
        else:
            command += ["-i", str(source), "-map", "0:v:0", "-map", "0:a:0?"]
            if max_width > 0:
                command += ["-vf", f"scale=w='min({max_width},iw)':h=-2:force_original_aspect_ratio=decrease"]
        if fps > 0:
            command += ["-r", str(fps)]
        command += ["-c:v", codec, "-c:a", self.settings.secondary_video_audio_codec, "-b:a", self.settings.secondary_video_audio_bitrate]
        if codec == "libvpx-vp9" and int(self.settings.secondary_video_crf) == 0:
            command += ["-lossless", "1"]
        else:
            command += ["-crf", str(max(0, int(self.settings.secondary_video_crf))), "-b:v", "0"]
        if codec in {"libvpx", "libvpx-vp9"}:
            command += ["-deadline", "good", "-cpu-used", str(max(0, int(self.settings.secondary_video_cpu_used)))]
        command.append(str(output))
        return command

    def _run(self, command: list[str]) -> None:
        logger.debug("Running FFmpeg: %s", " ".join(command))
        progress_command = command[:-1] + ["-progress", "pipe:2", "-nostats", command[-1]] if command else command
        process: subprocess.Popen[str] | None = None
        stderr_lines: list[str] = []
        progress_state = {"out_time_ms": None, "speed": None}
        started = time.monotonic()
        try:
            process = subprocess.Popen(  # noqa: S603 - FFmpegResolver validates the executable path
                [self.ffmpeg_bin, *progress_command[1:]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            if process.stderr is None:
                raise RuntimeError("FFmpeg stderr stream was not created")
            def consume_stderr() -> None:
                if process is None or process.stderr is None:
                    return
                for raw in process.stderr:
                    line = raw.strip()
                    if not line:
                        continue
                    stderr_lines.append(line)
                    if line.startswith("out_time_ms="):
                        try:
                            progress_state["out_time_ms"] = int(line.split("=", 1)[1])
                        except ValueError:
                            pass
                    elif line.startswith("speed="):
                        progress_state["speed"] = line.split("=", 1)[1].strip()
            reader = threading.Thread(target=consume_stderr, name="ffmpeg-stderr", daemon=True)
            reader.start()
            timeout = max(1, int(self.settings.ffmpeg_timeout_seconds))
            deadline = started + timeout
            last_log = started
            while process.poll() is None:
                now = time.monotonic()
                if now - last_log >= 15:
                    out_time = progress_state["out_time_ms"]
                    output_time = f"{int(out_time) / 1_000_000:.1f}s" if isinstance(out_time, int) else "unknown"
                    speed = progress_state["speed"] or "unknown"
                    logger.info("FFmpeg working: elapsed=%.0fs output_time=%s speed=%s", now - started, output_time, speed)
                    last_log = now
                if now >= deadline:
                    process.kill()
                    process.wait()
                    reader.join(timeout=2)
                    raise RuntimeError(f"FFmpeg conversion timed out after {timeout}s")
                time.sleep(0.25)
            reader.join(timeout=2)
            if process.returncode != 0:
                detail = next((line for line in reversed(stderr_lines) if not line.startswith(("frame=", "fps=", "out_", "progress="))), "FFmpeg conversion failed")
                raise RuntimeError(detail)
            logger.info("FFmpeg completed: elapsed=%.1fs", time.monotonic() - started)
        except FileNotFoundError as exc:
            raise RuntimeError("FFmpeg no está disponible. Configura FFMPEG_BIN o instala imageio-ffmpeg.") from exc
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                if process.stderr is not None and not process.stderr.closed:
                    process.stderr.close()

def _extract_progress_value(lines: list[str], key: str) -> str | None:
    prefix = f"{key}="
    for line in reversed(lines):
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None

def _format_duration(seconds: float) -> str:
    whole = max(0, int(seconds))
    hours, remainder = divmod(whole, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
