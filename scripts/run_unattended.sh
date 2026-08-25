#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
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
elif [[ -x ".venv/bin/python" ]]; then
  exec .venv/bin/python main.py "${args[@]}"
else
  echo "[ERROR] Ejecutable o Python no encontrado." >&2
  exit 1
fi
