from __future__ import annotations

import shutil
from pathlib import Path

from config.settings import BASE_DIR, AppSettings


class FFmpegResolver:
    """Resuelve FFmpeg sin obligar a instalarlo en el PATH del sistema."""

    @staticmethod
    def resolve(settings: AppSettings) -> Path:
        candidates: list[Path] = []

        configured = settings.ffmpeg_bin.strip()
        if configured:
            configured_path = Path(configured).expanduser()
            if configured_path.is_absolute() or any(sep in configured for sep in ("/", "\\")):
                if not configured_path.is_absolute():
                    configured_path = BASE_DIR / configured_path
                candidates.append(configured_path)
            else:
                configured_from_path = shutil.which(configured)
                if configured_from_path:
                    return Path(configured_from_path).resolve()

        name = "ffmpeg.exe" if __import__("sys").platform.startswith("win") else "ffmpeg"
        candidates.append(BASE_DIR / "tools" / "ffmpeg" / "bin" / name)

        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()

        try:
            import imageio_ffmpeg

            return Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
        except Exception as exc:
            system_ffmpeg = shutil.which("ffmpeg")
            if system_ffmpeg:
                return Path(system_ffmpeg).resolve()
            raise RuntimeError(
                "No se ha encontrado FFmpeg. Instala las dependencias del proyecto "
                "(`pip install -r requirements.txt`), coloca ffmpeg en "
                "tools/ffmpeg/bin/ o configura FFMPEG_BIN en .env."
            ) from exc

    @classmethod
    def doctor(cls, settings: AppSettings) -> dict[str, str | bool]:
        try:
            executable = cls.resolve(settings)
            return {"available": True, "path": str(executable)}
        except RuntimeError as exc:
            return {"available": False, "path": "", "error": str(exc)}
