#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -d venv ]]; then
    python3 -m venv venv
fi

venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements-dev.txt
venv/bin/python main.py init

echo "Comprobando FFmpeg mediante imageio-ffmpeg..."
venv/bin/python -c 'import imageio_ffmpeg; print("FFmpeg:", imageio_ffmpeg.get_ffmpeg_exe())'
venv/bin/python main.py doctor

echo "Entorno listo."
