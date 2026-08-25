#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -x "./dist/VideoTranslationPipeline/VideoTranslationPipeline" ]]; then
  exec ./dist/VideoTranslationPipeline/VideoTranslationPipeline run --scheduled
elif [[ -x "./VideoTranslationPipeline" ]]; then
  exec ./VideoTranslationPipeline run --scheduled
elif [[ -x ".venv/bin/python" ]]; then
  exec .venv/bin/python main.py run --scheduled
else
  echo "[ERROR] Ejecutable o Python no encontrado." >&2
  exit 1
fi
