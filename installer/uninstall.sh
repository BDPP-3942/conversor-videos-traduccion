#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${APPIMAGE:-}" && -f "$APPIMAGE" ]]; then
    target="$APPIMAGE"
elif [[ "$(uname -s)" == "Darwin" ]]; then
    script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
    target="$(cd -- "$script_dir/../.." && pwd)"
else
    script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
    if [[ "$script_dir" == *"/VideoTranslationPipeline.app/Contents/Resources" ]]; then
        target="$(cd -- "$script_dir/../.." && pwd)"
    else
        target="$script_dir"
    fi
fi

if [[ -z "$target" || "$target" == "/" || "$target" == "$HOME" ]]; then
    echo "Ruta de desinstalación no válida: $target" >&2
    exit 1
fi

printf 'Se eliminará la aplicación: %s\n' "$target"
rm -rf -- "$target"
