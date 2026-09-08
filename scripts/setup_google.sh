#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
command -v uv >/dev/null 2>&1 || { echo "[ERROR] uv no está instalado."; exit 1; }
[[ -d ".venv" ]] || { echo "[ERROR] Ejecuta primero scripts/setup_env.sh"; exit 1; }
uv sync --extra google
exec uv run python main.py auth google
