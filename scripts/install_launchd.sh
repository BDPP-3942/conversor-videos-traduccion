#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="${1:-com.video.translation.pipeline}"
shift || true
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

# Default: normal unattended processing. Additional arguments can define a reprocess task, e.g.:
# scripts/install_launchd.sh com.video.translation.reprocess reprocess-subtitles --scheduled --output-folder 37x02_Tema --stt-only
if [[ $# -eq 0 ]]; then
    PROGRAM_ARGS=(run --scheduled)
else
    PROGRAM_ARGS=("$@")
fi

xml_escape() {
    python3 - "$1" <<'PY'
import sys
print(sys.argv[1].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;"))
PY
}

{
    cat <<PLIST_HEADER
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>$(xml_escape "$LABEL")</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(xml_escape "$EXECUTABLE")</string>
PLIST_HEADER
    for arg in "${PROGRAM_ARGS[@]}"; do
        printf '        <string>%s</string>\n' "$(xml_escape "$arg")"
    done
    cat <<PLIST_FOOTER
    </array>
    <key>WorkingDirectory</key><string>$(xml_escape "$PROJECT_DIR")</string>
    <key>RunAtLoad</key><true/>
    <key>StartInterval</key><integer>300</integer>
    <key>StandardOutPath</key><string>$(xml_escape "$LOG_DIR/launchd.stdout.log")</string>
    <key>StandardErrorPath</key><string>$(xml_escape "$LOG_DIR/launchd.stderr.log")</string>
</dict>
</plist>
PLIST_FOOTER
} > "$PLIST_PATH"

launchctl bootout "gui/$(id -u)" "$PLIST_PATH" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
echo "[OK] launchd instalado: $LABEL"
echo "[INFO] Plist: $PLIST_PATH"
echo "[INFO] Ejecutable: $EXECUTABLE"
