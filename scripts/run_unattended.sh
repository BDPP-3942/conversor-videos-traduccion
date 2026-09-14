#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
if [[ "${1:-}" == "reprocess-subtitles" ]]; then
    shift
    args=(--scheduled "$@")
else
    args=(run --scheduled "$@")
fi
if [[ -x "./dist/VideoTranslationPipeline/VideoTranslationPipeline" ]]; then
  exec ./dist/VideoTranslationPipeline/VideoTranslationPipeline "${args[@]}"
elif [[ -x "./VideoTranslationPipeline" ]]; then
  exec ./VideoTranslationPipeline "${args[@]}"
elif [[ -d ".venv" ]]; then
  source "$PROJECT_DIR/scripts/lib/resolve_uv.sh"
  if UV_BIN="$(resolve_uv "$PROJECT_DIR")"; then
    exec "$UV_BIN" run python main.py "${args[@]}"
  elif [[ -x ".venv/bin/python" ]]; then
    exec .venv/bin/python main.py "${args[@]}"
  else
    echo "[ERROR] uv o Python no encontrado. Ejecuta scripts/setup_env.sh." >&2
    exit 1
  fi
else
  echo "[ERROR] Ejecutable, uv o Python no encontrado. Ejecuta scripts/setup_env.sh." >&2
  exit 1
fi
