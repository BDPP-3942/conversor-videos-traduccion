#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

INSTALL_CLOUD=false
INSTALL_RCLONE=false
PREFETCH_WHISPER=false
for arg in "$@"; do
    case "$arg" in
        --cloud) INSTALL_CLOUD=true ;;
        --rclone) INSTALL_RCLONE=true ;;
        --prefetch-whisper) PREFETCH_WHISPER=true ;;
        *) echo "[ERROR] Opción desconocida: $arg"; exit 2 ;;
    esac
done

find_python() {
    local candidates=()
    if [[ -n "${PYTHON_BIN:-}" ]]; then candidates+=("$PYTHON_BIN"); fi
    if [[ "$(uname -s)" == "Darwin" ]] && command -v pyenv >/dev/null 2>&1; then
        candidates+=("$(pyenv which python3 2>/dev/null || true)")
    fi
    candidates+=(python3.13 python3.12 python3.11 python3 python)
    for candidate in "${candidates[@]}"; do
        [[ -z "$candidate" ]] && continue
        if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)' >/dev/null 2>&1; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

PYTHON_BIN="$(find_python || true)"

if [[ -z "$PYTHON_BIN" ]] && [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
    echo "[INFO] Intentando instalar Python 3.13 mediante Homebrew..."
    brew install python@3.13
    BREW_PYTHON="$(brew --prefix python@3.13)/bin/python3.13"
    [[ -x "$BREW_PYTHON" ]] && PYTHON_BIN="$BREW_PYTHON"
fi

if [[ -z "$PYTHON_BIN" ]]; then
    echo "[ERROR] Se necesita Python 3.11, 3.12 o 3.13."
    exit 1
fi

echo "[INFO] Python seleccionado: $PYTHON_BIN"
"$PYTHON_BIN" --version

VENV_DIR="$PROJECT_DIR/.venv"
if [[ -x "$VENV_DIR/bin/python" ]] && ! "$VENV_DIR/bin/python" -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)'; then
    echo "[INFO] Eliminando entorno virtual incompatible..."
    rm -rf "$VENV_DIR"
fi
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "[INFO] Creando entorno virtual..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
"$VENV_PYTHON" --version
"$VENV_PYTHON" -c 'import tomllib'
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt
$INSTALL_CLOUD && "$VENV_PYTHON" -m pip install -r requirements-google.txt
$INSTALL_RCLONE && "$VENV_PYTHON" -m pip install -r requirements-rclone.txt

"$VENV_PYTHON" -c 'import imageio_ffmpeg; print("[OK] FFmpeg:", imageio_ffmpeg.get_ffmpeg_exe())'
if $INSTALL_RCLONE; then
    command -v rclone >/dev/null 2>&1 || { echo "[ERROR] rclone no está instalado. Ejecuta scripts/setup_rclone.sh"; exit 1; }
fi
"$VENV_PYTHON" main.py doctor
if $PREFETCH_WHISPER; then
    echo "[INFO] Precargando el modelo Whisper seleccionado automáticamente..."
    "$VENV_PYTHON" main.py prefetch-whisper
fi
printf '\n[OK] Entorno preparado correctamente.\n'
