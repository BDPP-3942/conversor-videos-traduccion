from __future__ import annotations

import argparse
import importlib
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = BASE_DIR / "tools" / "tts" / "kokoro-v1.0.onnx"
DEFAULT_VOICES = BASE_DIR / "tools" / "tts" / "voices-v1.0.bin"
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
ALLOWED_HOST = "github.com"


def _env_values() -> dict[str, str]:
    values = {"TTS_ENABLED": os.getenv("TTS_ENABLED", "")}
    env_file = BASE_DIR / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, raw = line.partition("=")
            if separator and key.strip() in {"TTS_ENABLED", "TTS_MODEL_PATH", "TTS_VOICES_PATH"}:
                values[key.strip()] = raw.strip().strip('"').strip("'")
    return values


def _resolve_configured_path(value: str, default: Path) -> Path:
    if not value:
        return default
    path = Path(value).expanduser()
    return path if path.is_absolute() else BASE_DIR / path


def _validate_download_url(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        raise ValueError(f"Se rechaza la descarga TTS desde una URL no fiable: {url}")


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size > 0:
        print(f"[OK] El recurso TTS ya existe: {destination}")
        return
    _validate_download_url(url)
    print(f"[INFO] Descargando recurso TTS: {url}")
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        dir=destination.parent,
    )
    temporary = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as temp:
            with requests.get(
                url,
                headers={"User-Agent": "video-translation-pipeline/setup"},
                stream=True,
                timeout=60,
            ) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        temp.write(chunk)
        if temporary.stat().st_size <= 0:
            raise RuntimeError(f"El recurso TTS descargado está vacío: {url}")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prepara los recursos TTS opcionales de Kokoro. "
            "Instala primero la dependencia de Python con uv."
        )
    )
    parser.add_argument(
        "--enable",
        action="store_true",
        help="Prepara TTS aunque TTS_ENABLED no esté establecido en true",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sustituye los archivos de modelo existentes",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="Ruta personalizada del modelo Kokoro",
    )
    parser.add_argument(
        "--voices-path",
        type=Path,
        default=None,
        help="Ruta personalizada del archivo de voces Kokoro",
    )
    args = parser.parse_args()

    env = _env_values()
    enabled = args.enable or env.get("TTS_ENABLED", "").lower() == "true"
    if not enabled:
        print("[INFO] TTS está desactivado; se omite la preparación de recursos Kokoro.")
        return 0

    try:
        importlib.import_module("kokoro_onnx")
    except ImportError as exc:
        raise RuntimeError(
            "Falta la dependencia de Kokoro. Ejecuta 'uv sync --extra tts' primero."
        ) from exc

    model_path = args.model_path or _resolve_configured_path(
        env.get("TTS_MODEL_PATH", ""),
        DEFAULT_MODEL,
    )
    voices_path = args.voices_path or _resolve_configured_path(
        env.get("TTS_VOICES_PATH", ""),
        DEFAULT_VOICES,
    )

    if args.force:
        model_path.unlink(missing_ok=True)
        voices_path.unlink(missing_ok=True)

    _download(MODEL_URL, model_path)
    _download(VOICES_URL, voices_path)
    print(f"[OK] Kokoro TTS preparado: {model_path} / {voices_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
