#!/bin/bash
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

# Launch kitty with class name for WM rules
kitty --class=gell-launcher \
--title "Gell Launcher" \
--override window_padding_width=0 \
--override window_margin_width=0 \
--override single_window_margin_width=0 \
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/app.py"