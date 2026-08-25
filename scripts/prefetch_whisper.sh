#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
if [[ -x ".venv/bin/python" ]]; then
    exec .venv/bin/python main.py prefetch-whisper
elif [[ -x "./dist/VideoTranslationPipeline/VideoTranslationPipeline" ]]; then
    exec ./dist/VideoTranslationPipeline/VideoTranslationPipeline prefetch-whisper
elif [[ -x "./VideoTranslationPipeline" ]]; then
    exec ./VideoTranslationPipeline prefetch-whisper
else
    echo "[ERROR] No se encuentra ni el entorno Python ni el ejecutable." >&2
    exit 1
fi
