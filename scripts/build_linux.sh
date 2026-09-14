#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
source "$PROJECT_DIR/scripts/lib/resolve_uv.sh"
UV_BIN="$(resolve_uv "$PROJECT_DIR")" || { echo "[ERROR] uv no está instalado. Ejecuta scripts/setup_env.sh." >&2; exit 1; }
NO_WEBM=false
if [[ "${1:-}" == "--no-webm" ]]; then NO_WEBM=true; fi
[[ -d ".venv" ]] || { echo "[ERROR] Ejecuta scripts/setup_env.sh"; exit 1; }
"$UV_BIN" sync --group dev --extra tts
"$UV_BIN" run python -m PyInstaller \
    --noconfirm --clean --onedir --name VideoTranslationPipeline \
    --collect-all faster_whisper \
    --collect-all ctranslate2 \
    --collect-all kokoro_onnx \
    --collect-all onnxruntime \
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
printf '%s\n' '[INFO] Los modelos Whisper/TTS permanecen externos y no se embeben en el ejecutable.'
