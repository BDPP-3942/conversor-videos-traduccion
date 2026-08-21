#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -x ".venv/bin/python" ]] || { echo "[ERROR] Ejecuta scripts/setup_env.sh"; exit 1; }
".venv/bin/python" -m pip install -r requirements-dev.txt
".venv/bin/python" -m PyInstaller --noconfirm --clean --onedir --name VideoTranslationPipeline main.py
mkdir -p dist/VideoTranslationPipeline/config dist/VideoTranslationPipeline/secrets dist/VideoTranslationPipeline/storage/input dist/VideoTranslationPipeline/storage/output dist/VideoTranslationPipeline/tools
cp config/app.toml dist/VideoTranslationPipeline/config/app.toml
cp .env.example dist/VideoTranslationPipeline/.env.example
cp -R storage/. dist/VideoTranslationPipeline/storage/
cp -R tools/. dist/VideoTranslationPipeline/tools/
printf '%s\n' '[OK] Aplicacion portable creada en dist/VideoTranslationPipeline/'
