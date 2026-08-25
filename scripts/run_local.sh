#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -x ".venv/bin/python" ]] || { echo "[ERROR] Ejecuta scripts/setup_env.sh"; exit 1; }
if [[ "${1:-}" == "reprocess-subtitles" ]]; then
    exec ".venv/bin/python" main.py "$@"
fi
exec ".venv/bin/python" main.py run "$@"
