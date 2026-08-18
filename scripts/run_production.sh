#!/usr/bin/env bash

set -e

cd "$(dirname "$0")/.."

echo "=========================================="
echo "MEDIA PIPELINE - PRODUCTION"
echo "=========================================="

./dist/MediaPipeline/media-pipeline \
    --source "ID_CARPETA_ORIGEN" \
    --target "ID_CARPETA_DESTINO" \
    --mode PRODUCTION