#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
NO_WEBM=false
if [[ "${1:-}" == "--no-webm" ]]; then
  NO_WEBM=true
fi
[[ -x ".venv/bin/python" ]] || { echo "[ERROR] Ejecuta scripts/setup_env.sh"; exit 1; }
".venv/bin/python" -m pip install -r requirements-dev.txt
".venv/bin/python" -m PyInstaller \
    --noconfirm --clean --onedir --name VideoTranslationPipeline \
    --collect-all faster_whisper \
    --collect-all ctranslate2 \
    --collect-all deep_translator \
    main.py
mkdir -p dist/VideoTranslationPipeline/config dist/VideoTranslationPipeline/secrets dist/VideoTranslationPipeline/storage dist/VideoTranslationPipeline/tools
cp config/app.toml dist/VideoTranslationPipeline/config/app.toml
if $NO_WEBM; then
  sed -i.bak 's/^generate_webm = true$/generate_webm = false/' dist/VideoTranslationPipeline/config/app.toml
  rm -f dist/VideoTranslationPipeline/config/app.toml.bak
fi
cp .env.example dist/VideoTranslationPipeline/.env.example
cp -R storage/. dist/VideoTranslationPipeline/storage/
cp -R tools/. dist/VideoTranslationPipeline/tools/
for d in input work output archive failures logs state; do mkdir -p "dist/VideoTranslationPipeline/storage/$d"; done
if $NO_WEBM; then printf '%s\n' '[INFO] WebM secundario desactivado en la configuracion empaquetada.'; fi
printf '%s\n' '[OK] Aplicacion portable creada en dist/VideoTranslationPipeline/'
printf '%s\n' '[INFO] Ejecuta: dist/VideoTranslationPipeline/VideoTranslationPipeline doctor'
printf '%s\n' '[INFO] Primera precarga: ./scripts/prefetch_whisper.sh'
printf '%s\n' '[INFO] El modelo Whisper permanece en la cache del usuario y no se incluye en el ejecutable.'
