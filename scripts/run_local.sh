#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v uv >/dev/null 2>&1 || { echo "[ERROR] uv no está instalado."; exit 1; }
[[ -d ".venv" ]] || { echo "[ERROR] Ejecuta scripts/setup_env.sh"; exit 1; }
exec uv run python scripts/run_local.py "$@"
