#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -x "./dist/VideoTranslationPipeline/VideoTranslationPipeline" ]]; then
  exec ./dist/VideoTranslationPipeline/VideoTranslationPipeline reprocess-subtitles "$@"
elif [[ -x "./VideoTranslationPipeline" ]]; then
  exec ./VideoTranslationPipeline reprocess-subtitles "$@"
elif [[ -x ".venv/bin/python" ]]; then
  exec .venv/bin/python main.py reprocess-subtitles "$@"
else
  echo "[ERROR] Ejecutable o Python no encontrado." >&2
  exit 1
fi
