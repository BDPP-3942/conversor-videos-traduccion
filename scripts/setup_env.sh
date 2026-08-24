#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

INSTALL_CLOUD=false
INSTALL_RCLONE=false
for arg in "$@"; do
    case "$arg" in
        --cloud) INSTALL_CLOUD=true ;;
        --rclone) INSTALL_RCLONE=true ;;
        *) echo "[ERROR] Opción desconocida: $arg"; exit 2 ;;
    esac
done

is_windows_shell() {
    [[ "$(uname -s)" =~ ^(MINGW|MSYS|CYGWIN) ]]
}

find_python() {
    local candidate

    if is_windows_shell && command -v py.exe >/dev/null 2>&1; then
        for version in 3.13 3.12 3.11; do
            if py.exe -"$version" -c \
                'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)' \
                >/dev/null 2>&1; then
                echo "py.exe -$version"
                return 0
            fi
        done
    fi

    for candidate in "${PYTHON_BIN:-}" python3.13 python3.12 python3.11 python3 python; do
        [[ -z "$candidate" ]] && continue
        if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c \
            'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)' \
            >/dev/null 2>&1; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

PYTHON_BIN="$(find_python || true)"

if [[ -z "$PYTHON_BIN" ]] && is_windows_shell && command -v winget.exe >/dev/null 2>&1; then
    echo "[INFO] Intentando instalar Python 3.13 mediante WinGet..."
    winget.exe install --id Python.Python.3.13 -e --scope user \
        --accept-source-agreements --accept-package-agreements --disable-interactivity
    [[ -d "${LOCALAPPDATA:-}/Programs/Python/Python313" ]] && \
        PATH="${LOCALAPPDATA}/Programs/Python/Python313:${LOCALAPPDATA}/Programs/Python/Python313/Scripts:$PATH"
    [[ -d "${LOCALAPPDATA:-}/Python/bin" ]] && \
        PATH="${LOCALAPPDATA}/Python/bin:$PATH"
    hash -r 2>/dev/null || true
    PYTHON_BIN="$(find_python || true)"
elif [[ -z "$PYTHON_BIN" ]] && [[ "$(uname -s)" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
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
$PYTHON_BIN --version

VENV_DIR="$PROJECT_DIR/.venv"
if [[ -x "$VENV_DIR/bin/python" ]] && ! "$VENV_DIR/bin/python" -c \
    'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] < (3,14) else 1)'; then
    echo "[INFO] Eliminando entorno virtual incompatible..."
    rm -rf "$VENV_DIR"
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "[INFO] Creando entorno virtual..."
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
"$VENV_PYTHON" --version
"$VENV_PYTHON" -c 'import tomllib; print("[OK] tomllib disponible")'

"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt
if $INSTALL_CLOUD; then
    "$VENV_PYTHON" -m pip install -r requirements-google.txt
fi

"$VENV_PYTHON" -c 'import imageio_ffmpeg; print("[OK] FFmpeg:", imageio_ffmpeg.get_ffmpeg_exe())'
"$VENV_PYTHON" main.py doctor

if $INSTALL_RCLONE; then
    command -v rclone >/dev/null 2>&1 || {
        echo "[ERROR] rclone no está instalado. Ejecuta scripts/setup_rclone.sh"
        exit 1
    }
fi

printf '\n[OK] Entorno preparado correctamente.\n'
printf 'Para activarlo: source .venv/bin/activate\n'
