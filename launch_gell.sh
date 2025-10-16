#!/bin/bash

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
CLASS_NAME="gell"
WAL_CACHE="$HOME/.cache/wal/colors.json"
WATCHER_PID_FILE="/tmp/gell_watcher.pid"

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

stop_watcher() {
    if [ -f "$WATCHER_PID_FILE" ]; then
        WATCHER_PID=$(cat "$WATCHER_PID_FILE")
        if kill -0 "$WATCHER_PID" 2>/dev/null; then
            kill "$WATCHER_PID" 2>/dev/null
            # Also kill the inotifywait child process
            pkill -P "$WATCHER_PID" 2>/dev/null
        fi
        rm -f "$WATCHER_PID_FILE"
    fi
}

start_watcher() {
    if ! command -v inotifywait >/dev/null 2>&1; then
        echo "⚠️  inotifywait not found. Install it with: sudo apt install inotify-tools"
        return
    fi

    (
        echo $$ > "$WATCHER_PID_FILE"
        inotifywait -m -e close_write "$WAL_CACHE" 2>/dev/null | while read -r _ _ _; do
            echo "🎨 Pywal theme changed — restarting Gell..."
            kill_gell
            sleep 0.2
            launch_gell
        done
    ) &
    
    disown
}

# Handle --prewarm flag
if [ "$1" = "--prewarm" ]; then
    kill_gell
    launch_gell
    exit 0
fi

# Check if window already exists
WINDOW_EXISTS=$(hyprctl clients | grep -c "class: $CLASS_NAME")
if [ "$WINDOW_EXISTS" -gt 0 ]; then
    kill_gell
fi

# Stop any existing watcher to prevent duplicates
stop_watcher

# Launch the app
launch_gell

# Start the theme watcher
start_watcher

exit 0