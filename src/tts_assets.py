from __future__ import annotations

import shutil
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
ALLOWED_HOST = "github.com"


def _download(url: str, destination: Path) -> None:
    if destination.is_file() and destination.stat().st_size > 0:
        return
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        raise ValueError(f"Se rechaza la descarga TTS desde una URL no fiable: {url}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f".{destination.name}.", dir=destination.parent, delete=False) as temp:
        temporary = Path(temp.name)
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "video-translation-pipeline/1"}),
                timeout=60,
            ) as response:
                shutil.copyfileobj(response, temp)
            if temporary.stat().st_size <= 0:
                raise RuntimeError(f"El recurso TTS descargado está vacío: {url}")
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)


def ensure_tts_assets(model_path: Path, voices_path: Path) -> tuple[Path, Path]:
    """Descarga de forma atómica los recursos Kokoro requeridos por TTS."""
    _download(MODEL_URL, model_path)
    _download(VOICES_URL, voices_path)
    return model_path, voices_path
