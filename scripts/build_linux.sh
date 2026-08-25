#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -x ".venv/bin/python" ]] || { echo "[ERROR] Ejecuta scripts/setup_env.sh"; exit 1; }
".venv/bin/python" -m pip install -r requirements-dev.txt
".venv/bin/python" -m PyInstaller --noconfirm --clean --onedir --name VideoTranslationPipeline main.py
mkdir -p dist/VideoTranslationPipeline/config dist/VideoTranslationPipeline/secrets dist/VideoTranslationPipeline/storage dist/VideoTranslationPipeline/tools
cp config/app.toml dist/VideoTranslationPipeline/config/app.toml
cp .env.example dist/VideoTranslationPipeline/.env.example
cp -R storage/. dist/VideoTranslationPipeline/storage/
cp -R tools/. dist/VideoTranslationPipeline/tools/
for d in input work output archive failures logs state; do mkdir -p "dist/VideoTranslationPipeline/storage/$d"; done
printf '%s
' '[OK] Aplicacion portable creada en dist/VideoTranslationPipeline/'
printf '%s
' '[INFO] Ejecuta: dist/VideoTranslationPipeline/VideoTranslationPipeline doctor'
printf '%s
' '[INFO] Primera precarga: ./scripts/prefetch_whisper.sh'
printf '%s
' '[INFO] El modelo Whisper permanece en la cache del usuario y no se incluye en el ejecutable.'
