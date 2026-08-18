#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/.."

VENV_DIR="venv"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[ERROR] No existe el venv."
    echo "Ejecuta primero:"
    echo "./scripts/setup_env.sh"
    exit 1
fi

source "$VENV_DIR/bin/activate"

read -p \
    "Introduce el ID de la carpeta ORIGEN de Google Drive: " \
    DRIVE_SOURCE

read -p \
    "Introduce el ID de la carpeta DESTINO de Google Drive: " \
    DRIVE_TARGET

read -p \
    "Selecciona modo (LOCAL / PRODUCTION) [LOCAL]: " \
    EXEC_MODE

EXEC_MODE=${EXEC_MODE:-LOCAL}

python3 main.py \
    --source "$DRIVE_SOURCE" \
    --target "$DRIVE_TARGET" \
    --mode "$EXEC_MODE"