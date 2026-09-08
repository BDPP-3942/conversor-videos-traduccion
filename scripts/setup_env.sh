#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

INSTALL_CLOUD=false
INSTALL_RCLONE=false
INSTALL_TTS=false
PREFETCH_WHISPER=false
for arg in "$@"; do
    case "$arg" in
        --cloud) INSTALL_CLOUD=true ;;
        --rclone) INSTALL_RCLONE=true ;;
        --tts) INSTALL_TTS=true ;;
        --prefetch-whisper) PREFETCH_WHISPER=true ;;
        *) echo "[ERROR] Opción desconocida: $arg"; exit 2 ;;
    esac
done

if ! command -v uv >/dev/null 2>&1; then
    echo "[ERROR] uv no está instalado. Instálalo desde https://docs.astral.sh/uv/ y vuelve a ejecutar este script."
    exit 1
fi

PYTHON_VERSION="${PYTHON_VERSION:-3.13}"
case "$PYTHON_VERSION" in
    3.11|3.12|3.13) ;;
    *) echo "[ERROR] PYTHON_VERSION debe ser 3.11, 3.12 o 3.13."; exit 2 ;;
esac

echo "[INFO] uv: $(uv --version)"
echo "[INFO] Python solicitado: $PYTHON_VERSION"
uv python install "$PYTHON_VERSION"
uv venv --python "$PYTHON_VERSION"
uv sync --python "$PYTHON_VERSION" --group dev ${INSTALL_CLOUD:+}

if $INSTALL_CLOUD; then
    uv sync --python "$PYTHON_VERSION" --group dev --extra google
fi
if $INSTALL_TTS; then
    uv sync --python "$PYTHON_VERSION" --group dev --extra tts
fi

uv run python -c 'import imageio_ffmpeg; print("[OK] FFmpeg:", imageio_ffmpeg.get_ffmpeg_exe())'
if $INSTALL_RCLONE; then
    command -v rclone >/dev/null 2>&1 || { echo "[ERROR] rclone no está instalado. Ejecuta scripts/setup_rclone.sh"; exit 1; }
fi

uv run python scripts/setup_tts.py
$INSTALL_TTS && uv run python scripts/setup_tts.py --enable

uv run python main.py doctor
if $PREFETCH_WHISPER; then
    echo "[INFO] Precargando el modelo Whisper seleccionado automáticamente..."
    uv run python main.py prefetch-whisper
fi
printf '\n[OK] Entorno preparado correctamente con uv.\n'
