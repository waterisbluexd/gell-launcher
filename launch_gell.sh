#!/bin/bash

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
CLASS_NAME="gell"
WAL_COLORS="$HOME/.cache/wal/colors-kitty.conf"
PID_FILE="/tmp/gell_launcher.pid"

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
    
    GELL_PID=$!
    echo $GELL_PID > "$PID_FILE"
    
    sleep 0.2
    hyprctl dispatch movetoworkspacesilent special:gell,class:$CLASS_NAME
}

kill_gell() {
    pkill -f "kitty --class=$CLASS_NAME" 2>/dev/null
    pkill -f "inotifywait.*$WAL_COLORS" 2>/dev/null
    rm -f "$PID_FILE"
    sleep 0.1
}

restart_gell() {
    echo "🔄 Restarting Gell with new theme..."
    kill_gell
    sleep 0.2
    launch_gell
}

watch_theme_changes() {
    if ! command -v inotifywait >/dev/null 2>&1; then
        echo "⚠️  inotifywait not found. Theme auto-reload disabled."
        echo "   Install with: sudo apt install inotify-tools"
        return
    fi
    
    # Watch for theme file changes in background
    (
        while true; do
            # Only watch for close_write event to avoid duplicates
            inotifywait -e close_write "$WAL_COLORS" 2>/dev/null
            
            # Small delay to debounce multiple writes
            sleep 0.1
            
            # Check if Gell is still running
            if [ -f "$PID_FILE" ]; then
                GELL_PID=$(cat "$PID_FILE")
                if kill -0 "$GELL_PID" 2>/dev/null; then
                    echo "🎨 Theme changed - reloading Gell..."
                    restart_gell
                else
                    # Gell died, stop watching
                    break
                fi
            else
                # PID file gone, stop watching
                break
            fi
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

# Launch the app
launch_gell

# Start watching for theme changes
watch_theme_changes

exit 0