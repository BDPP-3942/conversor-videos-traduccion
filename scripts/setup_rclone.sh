#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
[[ -x ".venv/bin/python" ]] || { echo "[ERROR] Ejecuta primero scripts/setup_env.sh"; exit 1; }
exec .venv/bin/python main.py provider bootstrap
