SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
CLASS_NAME="gell"
WAL_CACHE="$HOME/.cache/wal/colors.json"

launch_gell() {
    kitty \
        --class="$CLASS_NAME" \
        --title="Gell" \
        --override window_padding_width=0 \
        --override window_margin_width=0 \
        --override single_window_margin_width=0 \
        -o initial_window_width=80c \
        -o initial_window_height=25c \
        -o remember_window_size=no \
        "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/app.py" &
    sleep 0.2
    hyprctl dispatch movetoworkspacesilent special:gell,class:$CLASS_NAME
}

kill_gell() {
    pkill -f "kitty --class=$CLASS_NAME" 2>/dev/null
    sleep 0.1
}

if [ "$1" = "--prewarm" ]; then
    kill_gell
    launch_gell
    exit 0
fi
WINDOW_EXISTS=$(hyprctl clients | grep -c "class: $CLASS_NAME")
if [ "$WINDOW_EXISTS" -gt 0 ]; then
    kill_gell
fi
launch_gell
if command -v inotifywait >/dev/null 2>&1; then
    (
        inotifywait -m -e close_write "$WAL_CACHE" | while read -r _ _ _; do
            echo "🎨 Pywal theme changed — restarting Gell..."
            kill_gell
            launch_gell
        done
    ) >/dev/null 2>&1 &
else
    echo "⚠️  inotifywait not found. Install it with: sudo apt install inotify-tools"
fi
disown
exit 0
