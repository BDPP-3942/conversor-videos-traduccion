#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

INSTALL_CLOUD=false
INSTALL_RCLONE=false
INSTALL_TTS=false
PREFETCH_WHISPER=false
INSTALL_LOCAL_TRANSLATION=false

for arg in "$@"; do
    case "$arg" in
        --cloud) INSTALL_CLOUD=true ;;
        --rclone) INSTALL_RCLONE=true ;;
        --tts) INSTALL_TTS=true ;;
        --prefetch-whisper) PREFETCH_WHISPER=true ;;
        --local-translation) INSTALL_LOCAL_TRANSLATION=true ;;
        *) echo "[ERROR] Opción desconocida: $arg"; exit 2 ;;
    esac
done

LOCAL_UV_DIR="$PROJECT_DIR/tools/uv"
LOCAL_UV_BIN="$LOCAL_UV_DIR/uv"

if [[ -x "$LOCAL_UV_BIN" ]]; then
    UV_BIN="$LOCAL_UV_BIN"
    echo "[INFO] Usando uv gestionado por el proyecto: $UV_BIN"
elif command -v uv >/dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
    echo "[INFO] Usando uv disponible en PATH: $UV_BIN"
else
    if ! command -v curl >/dev/null 2>&1; then
        echo "[ERROR] No se encontró uv en PATH y curl es necesario para instalar uv localmente."
        exit 1
    fi
    echo "[INFO] uv no está disponible en PATH; instalando una copia gestionada en tools/uv/..."
    mkdir -p "$LOCAL_UV_DIR"
    if ! curl -LsSf https://astral.sh/uv/install.sh | env UV_UNMANAGED_INSTALL="$LOCAL_UV_DIR" sh; then
        echo "[ERROR] No se pudo instalar uv en $LOCAL_UV_DIR."
        exit 1
    fi
    if [[ ! -x "$LOCAL_UV_BIN" ]]; then
        echo "[ERROR] El instalador de uv terminó sin producir $LOCAL_UV_BIN."
        exit 1
    fi
    UV_BIN="$LOCAL_UV_BIN"
    echo "[OK] uv instalado localmente: $UV_BIN"
fi

PYTHON_VERSION="${PYTHON_VERSION:-3.13}"
case "$PYTHON_VERSION" in
    3.11|3.12|3.13) ;;
    *) echo "[ERROR] PYTHON_VERSION debe ser 3.11, 3.12 o 3.13."; exit 2 ;;
esac

echo "[INFO] uv: $("$UV_BIN" --version)"
echo "[INFO] Python solicitado: $PYTHON_VERSION"
"$UV_BIN" python install "$PYTHON_VERSION"
"$UV_BIN" venv --python "$PYTHON_VERSION"
"$UV_BIN" sync --python "$PYTHON_VERSION" --group dev

if $INSTALL_CLOUD; then
    "$UV_BIN" sync --python "$PYTHON_VERSION" --group dev --extra google
fi
if $INSTALL_TTS; then
    "$UV_BIN" sync --python "$PYTHON_VERSION" --group dev --extra tts
fi

"$UV_BIN" run python -c 'import imageio_ffmpeg; print("[OK] FFmpeg:", imageio_ffmpeg.get_ffmpeg_exe())'
if $INSTALL_RCLONE; then
    echo "[INFO] Preparando el binario rclone gestionado por el proyecto..."
    "$UV_BIN" run python main.py provider bootstrap
fi

"$UV_BIN" run python scripts/setup_tts.py
$INSTALL_TTS && "$UV_BIN" run python scripts/setup_tts.py --enable

"$UV_BIN" run python main.py doctor
if $PREFETCH_WHISPER; then
    echo "[INFO] Precargando el modelo Whisper seleccionado automáticamente..."
    "$UV_BIN" run python main.py prefetch-whisper
fi
if $INSTALL_LOCAL_TRANSLATION; then
    echo "[INFO] Preparando el modelo de traducción local fijado..."
    "$UV_BIN" run python scripts/manage_local_translation.py download
    "$UV_BIN" run python scripts/manage_local_translation.py status
fi
printf '\n[OK] Entorno preparado correctamente con uv.\n'
