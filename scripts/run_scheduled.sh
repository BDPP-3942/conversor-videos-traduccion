#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -x "venv/bin/python" ]] || exit 1
exec "venv/bin/python" main.py run --config config/app.toml
