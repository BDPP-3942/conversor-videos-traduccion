#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
source "$PROJECT_DIR/scripts/lib/resolve_uv.sh"
UV_BIN="$(resolve_uv "$PROJECT_DIR")" || { echo "[ERROR] uv no está instalado. Ejecuta scripts/setup_env.sh primero." >&2; exit 1; }
exec "$UV_BIN" run python main.py provider bootstrap
