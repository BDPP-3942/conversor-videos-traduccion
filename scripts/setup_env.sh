#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
VENV_DIR="venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[INFO] Creando entorno virtual en Linux..."
    python3 -m venv "$VENV_DIR"
fi

echo "[INFO] Activando entorno e instalando dependencias desde requirements.txt..."
source "$VENV_DIR/bin/activate"
python3 -m pip install --upgrade pip
pip install -r requirements.txt

echo "[OK] Entorno virtual Linux desplegado correctamente."
