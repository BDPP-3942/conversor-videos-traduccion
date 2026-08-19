#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -d venv ]] || python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -r requirements-dev.txt
venv/bin/python main.py init
venv/bin/python main.py doctor || true
echo "Entorno listo."
