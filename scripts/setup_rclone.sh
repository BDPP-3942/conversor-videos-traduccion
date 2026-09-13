#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
command -v uv >/dev/null 2>&1 || { echo "[ERROR] uv no está instalado. Ejecuta scripts/setup_env.sh primero."; exit 1; }
exec uv run python main.py provider bootstrap
