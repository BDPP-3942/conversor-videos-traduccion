#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="${1:-com.video.translation.pipeline}"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/$LABEL.plist"
LOG_DIR="$PROJECT_DIR/storage/logs"
mkdir -p "$PLIST_DIR" "$LOG_DIR"

EXECUTABLE="$PROJECT_DIR/dist/VideoTranslationPipeline/VideoTranslationPipeline"
if [[ ! -x "$EXECUTABLE" ]]; then
    EXECUTABLE="$PROJECT_DIR/VideoTranslationPipeline"
fi
if [[ ! -x "$EXECUTABLE" ]]; then
    echo "[ERROR] No se encuentra el ejecutable. Ejecuta scripts/build_linux.sh primero." >&2
    exit 1
fi

cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$EXECUTABLE</string>
        <string>run</string>
        <string>--scheduled</string>
    </array>
    <key>WorkingDirectory</key><string>$PROJECT_DIR</string>
    <key>RunAtLoad</key><true/>
    <key>StartInterval</key><integer>300</integer>
    <key>StandardOutPath</key><string>$LOG_DIR/launchd.stdout.log</string>
    <key>StandardErrorPath</key><string>$LOG_DIR/launchd.stderr.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
echo "[OK] launchd instalado: $LABEL"
echo "[INFO] Plist: $PLIST_PATH"
echo "[INFO] Ejecutable: $EXECUTABLE"
