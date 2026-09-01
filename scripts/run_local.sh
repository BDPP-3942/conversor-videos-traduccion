#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -x ".venv/bin/python" ]] || { echo "[ERROR] Ejecuta scripts/setup_env.sh"; exit 1; }
case "${1:-run}" in
  reprocess-subtitles|duplicates)
    exec ".venv/bin/python" scripts/run_local.py "$@"
    ;;
  *)
    exec ".venv/bin/python" scripts/run_local.py "$@"
    ;;
esac
