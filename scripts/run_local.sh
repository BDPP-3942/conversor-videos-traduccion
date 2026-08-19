#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x "venv/bin/python" ]]; then
  echo "[ERROR] No existe venv. Ejecuta scripts/setup_env.sh"
  exit 1
fi
"venv/bin/python" main.py run --provider local
