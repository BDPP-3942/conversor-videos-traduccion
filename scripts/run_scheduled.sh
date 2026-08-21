#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -x ".venv/bin/python" ]] || { echo "[ERROR] Ejecuta scripts/setup_env.sh --cloud"; exit 1; }
exec ".venv/bin/python" main.py run --mode cloud --config config/app.toml "$@"
