#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -x ".venv/bin/python" ]] || { echo "[ERROR] Ejecuta primero scripts/setup_env.sh"; exit 1; }
".venv/bin/python" -m pip install -r requirements-google.txt
exec ".venv/bin/python" main.py auth google
