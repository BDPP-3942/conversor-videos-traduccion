from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = BASE_DIR / "tools" / "tts" / "kokoro-v1.0.onnx"
DEFAULT_VOICES = BASE_DIR / "tools" / "tts" / "voices-v1.0.bin"
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"


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


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size > 0:
        print(f"[OK] TTS asset already exists: {destination}")
        return
    print(f"[INFO] Downloading TTS asset: {url}")
    request = Request(url, headers={"User-Agent": "video-translation-pipeline/setup"})
    with tempfile.NamedTemporaryFile(prefix=f".{destination.name}.", dir=destination.parent, delete=False) as temp:
        temporary = Path(temp.name)
        try:
            # Fixed GitHub release asset URL; shell execution is not involved.
            with urlopen(request, timeout=60) as response:  # noqa: S310
                while chunk := response.read(1024 * 1024):
                    temp.write(chunk)
            if temporary.stat().st_size <= 0:
                raise RuntimeError(f"Downloaded empty TTS asset: {url}")
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the optional Kokoro TTS dependency and model files.")
    parser.add_argument("--enable", action="store_true", help="Install/bootstrap TTS even when TTS_ENABLED is not true.")
    parser.add_argument("--force", action="store_true", help="Replace existing model files.")
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--voices-path", type=Path, default=None)
    args = parser.parse_args()

    env = _env_values()
    enabled = args.enable or env.get("TTS_ENABLED", "").lower() == "true"
    if not enabled:
        print("[INFO] TTS is disabled; skipping Kokoro installation.")
        return 0

    model_path = args.model_path or _resolve_configured_path(env.get("TTS_MODEL_PATH", ""), DEFAULT_MODEL)
    voices_path = args.voices_path or _resolve_configured_path(env.get("TTS_VOICES_PATH", ""), DEFAULT_VOICES)

    print("[INFO] Installing optional Kokoro TTS dependency...")
    subprocess.run(  # noqa: S603 -- executable is the active Python interpreter and arguments are fixed.
        [sys.executable, "-m", "pip", "install", "-e", ".[tts]"],
        cwd=BASE_DIR,
        check=True,
    )

    if args.force:
        model_path.unlink(missing_ok=True)
        voices_path.unlink(missing_ok=True)

    _download(MODEL_URL, model_path)
    _download(VOICES_URL, voices_path)
    print(f"[OK] Kokoro TTS ready: {model_path} / {voices_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
