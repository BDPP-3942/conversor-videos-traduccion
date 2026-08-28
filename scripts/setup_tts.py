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


def _env_enabled() -> bool:
    value = os.getenv("TTS_ENABLED", "").strip().lower()
    env_file = BASE_DIR / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            key, separator, raw = line.partition("=")
            if separator and key.strip() == "TTS_ENABLED":
                value = raw.strip().strip('"').strip("'").lower()
    return value == "true"


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
            with urlopen(request, timeout=60) as response:
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
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--voices-path", type=Path, default=DEFAULT_VOICES)
    args = parser.parse_args()

    if not args.enable and not _env_enabled():
        print("[INFO] TTS is disabled; skipping Kokoro installation.")
        return 0

    print("[INFO] Installing optional Kokoro TTS dependency...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[tts]"], cwd=BASE_DIR, check=True)

    if args.force:
        args.model_path.unlink(missing_ok=True)
        args.voices_path.unlink(missing_ok=True)

    _download(MODEL_URL, args.model_path)
    _download(VOICES_URL, args.voices_path)
    print(f"[OK] Kokoro TTS ready: {args.model_path} / {args.voices_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
