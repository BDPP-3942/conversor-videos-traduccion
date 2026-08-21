#!/usr/bin/env bash
set -euo pipefail
command -v rclone >/dev/null 2>&1 || { echo "[ERROR] rclone no está instalado. Instálalo desde https://rclone.org/"; exit 1; }
rclone version
echo "[OK] rclone disponible. Ejecuta: rclone config"
