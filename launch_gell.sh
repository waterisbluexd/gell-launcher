#!/bin/bash
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
CLASS_NAME="gell-launcher"

WINDOW_EXISTS=$(hyprctl clients | grep -c "class: $CLASS_NAME")

if [ "$WINDOW_EXISTS" -gt 0 ]; then
    hyprctl dispatch togglespecialworkspace gell
else
    kitty \
        --class="$CLASS_NAME" \
        --title="Gell Launcher" \
        --override window_padding_width=0 \
        --override window_margin_width=0 \
        --override single_window_margin_width=0 \
        -o initial_window_width=80c \
        -o initial_window_height=25c \
        -o remember_window_size=no \
        "$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/app.py" &
fi