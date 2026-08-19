#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -x venv/bin/python ]] || { echo "Ejecuta primero scripts/setup_env.sh"; exit 1; }
venv/bin/python main.py auth google
