#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -x venv/bin/python ]] || { echo "Ejecuta scripts/setup_env.sh"; exit 1; }
venv/bin/python -m PyInstaller --noconfirm --clean --onedir --name VideoTranslationPipeline main.py
mkdir -p dist/VideoTranslationPipeline/storage/input dist/VideoTranslationPipeline/storage/output
echo "Ejecutable creado en dist/VideoTranslationPipeline/"
