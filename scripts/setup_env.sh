#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

MIN_MAJOR=3
MIN_MINOR=11

find_python() {
    local candidates=(
        "${PYTHON_BIN:-}"
        python3.14
        python3.13
        python3.12
        python3.11
        python3
        python
    )

    for candidate in "${candidates[@]}"; do
        [[ -z "$candidate" ]] && continue

        if command -v "$candidate" >/dev/null 2>&1; then
            if "$candidate" -c \
                'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'
            then
                echo "$candidate"
                return 0
            fi
        fi
    done

    return 1
}

PYTHON_BIN="$(find_python || true)"

# macOS: intentar instalar Python mediante Homebrew
if [[ -z "$PYTHON_BIN" ]] && [[ "$(uname -s)" == "Darwin" ]]; then
    if command -v brew >/dev/null 2>&1; then
        echo "[INFO] No se encontró Python >= 3.11."
        echo "[INFO] Intentando instalar Python 3.13 mediante Homebrew..."

        brew install python@3.13

        BREW_PYTHON="$(brew --prefix python@3.13)/bin/python3.13"

        if [[ -x "$BREW_PYTHON" ]]; then
            PYTHON_BIN="$BREW_PYTHON"
        fi
    fi
fi

if [[ -z "$PYTHON_BIN" ]]; then
    echo
    echo "[ERROR] Se necesita Python 3.11 o superior."
    echo
    echo "Instala Python 3.13 y vuelve a ejecutar este script."
    echo "En macOS con Homebrew:"
    echo "  brew install python@3.13"
    exit 1
fi

echo "[INFO] Python seleccionado:"
"$PYTHON_BIN" --version

VENV_DIR="$PROJECT_DIR/.venv"

# Eliminar un entorno creado previamente con una versión incompatible
if [[ -x "$VENV_DIR/bin/python" ]]; then
    if ! "$VENV_DIR/bin/python" -c \
        'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'
    then
        echo "[INFO] El entorno virtual existente usa una versión incompatible."
        rm -rf "$VENV_DIR"
    fi
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "[INFO] Creando entorno virtual..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"

echo "[INFO] Python del entorno:"
"$VENV_PYTHON" --version

"$VENV_PYTHON" -c 'import tomllib; print("[OK] tomllib disponible")'

echo "[INFO] Actualizando pip..."
"$VENV_PYTHON" -m pip install --upgrade pip

echo "[INFO] Instalando dependencias..."
"$VENV_PYTHON" -m pip install -r requirements.txt

echo "[INFO] Verificando FFmpeg..."
"$VENV_PYTHON" -c \
'import imageio_ffmpeg; print("[OK] FFmpeg:", imageio_ffmpeg.get_ffmpeg_exe())'

echo "[INFO] Ejecutando doctor..."
"$VENV_PYTHON" main.py doctor

echo
echo "[OK] Entorno preparado."
echo
echo "Para activarlo:"
echo "  source .venv/bin/activate"