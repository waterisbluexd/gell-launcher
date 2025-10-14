"""
Theme module: Handles pywal color loading and CSS generation.
"""
import os
from pathlib import Path


def load_wal_colors(config_path: str = '/home/wib/.cache/wal/colors-kitty.conf') -> dict[str, str]:
    """Parse pywal's kitty color config and return a dict of color names to hex values."""
    colors = {}
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0]
                    value = parts[1]
                    if value.startswith('#'):
                        colors[key] = value
    except FileNotFoundError:
        print(f"Warning: Could not find {config_path}")
        colors = {
            'background': "#000000",
            'foreground': '#ffffff',
            'cursor': '#ffffff',
            **{f'color{i}': '#888888' for i in range(16)}
        }
    return colors


def generate_css(colors: dict[str, str]) -> str:
    """Generate complete CSS string from color dictionary."""
    # Base colors
    bg = colors.get('background', '#000000')
    fg = colors.get('foreground', '#ffffff')
    cursor = colors.get('cursor', fg)

    # Terminal colors
    c0 = colors.get('color0', '#000000')
    c1 = colors.get('color1', '#ff0000')
    c2 = colors.get('color2', '#00ff00')
    c3 = colors.get('color3', '#ffff00')
    c4 = colors.get('color4', '#0000ff')
    c5 = colors.get('color5', '#ff00ff')
    c6 = colors.get('color6', '#00ffff')
    c7 = colors.get('color7', '#ffffff')
    c8 = colors.get('color8', '#888888')
    c9 = colors.get('color9', '#ff8888')
    c10 = colors.get('color10', '#88ff88')
    c11 = colors.get('color11', '#ffff88')
    c12 = colors.get('color12', '#8888ff')
    c13 = colors.get('color13', '#ff88ff')
    c14 = colors.get('color14', '#88ffff')
    c15 = colors.get('color15', '#ffffff')

    return f"""
/* ========================================
   MAIN CONTAINER
   ======================================== */
#gell-container {{
    width: 100%;
    height: 100%;
    max-width: 100;
    min-height: 25;
    padding_left: 1;
    padding_right: 1;
    background: {c0};
}}

/* ========================================
   PANEL CONTAINERS
   ======================================== */
#Gell {{
    height: 30%;
    border: solid {c3};
    border-title-align: left;
    border-title-color: {c6};
    border-title-style: bold;
}}

#Apps {{
    height: 64%;
    border: solid {c3};
    border-title-align: left;
    border-title-color: {c6};
    border-title-style: bold;
}}

#Input {{
    height: 6%;
    border: solid {c3};
    border-title-align: left;
    border-title-color: {c6};
    border-title-style: bold;
}}

/* ========================================
   APP LIST
   ======================================== */
#app-list {{
    background: {c0};
    overflow-y: hidden;
    padding_left: 2;
    padding_right: 2;
}}

#app-list:focus {{
    background: transparent;
}}

ListView > ListItem.-highlight {{
    background: {c1};
}}

/* ========================================
   SEARCH INPUT
   ======================================== */
.panel-content {{
    width: 100%;
    height: 100%;
}}

#search-input {{
    width: 100%;
    border: none;
}}

#search-input > .input--placeholder {{
    color: {c8};
    text-style: italic;
}}

#search-input > .input--cursor {{
    color: {c0};
    text-style: bold;
}}

Input {{
    background: transparent;
}}

Input:focus {{
    border: none;
}}

/* ========================================
   MUSIC PLAYER PANEL
   ======================================== */
.music-main-container {{
    layout: vertical; /* Use a vertical layout */
    width: 100%;
    height: 100%;
    padding: 1 2;
    margin-top: 0;
}}

.music-no-media {{
    color: {c6};
    text-align: center;
    text-style: bold;
    margin-top: 2;
}}

.music-title {{
    color: {fg};
    text-style: bold;
    margin-bottom: 0;
    text-align: center;
    max-height: 2;
    overflow-y: hidden;
    text-overflow: ellipsis;
}}

.music-artist {{
    color: {c10};
    height: 1fr; /* Fill available vertical space */
    width: 100%;
    margin-bottom: 0;
    text-align: center;
    content-align: center middle; /* Vertically center artist text */
}}

.music-progress-container {{
    height: 1;
    width: 100%;
    margin-top: 1;
    margin-bottom: 0;
    align: center middle;
}}

.music-time {{
    color: {c8};
    width: auto;
}}

.music-progress-bar {{
    color: {c3};
    width: 1fr;
    text-align: center;
}}

.music-control-buttons {{
    height: auto;
    width: 100%;
    align: center middle;
    margin-top: 1;
}}

/* ========================================
   BUTTON STYLING - PREVIOUS & NEXT
   ======================================== */
Button.music-btn-main {{
    width: 5;
    height: 3;
    min-width: 5;
    max-width: 5;
    padding: 0 0;
    content-align: center middle;
    background: transparent;
    color: {c6};              /* Cyan text */
    border: solid {c8};       /* Dark gray border */
    margin: 0 1;
}}

Button.music-btn-main:hover {{
    background: transparent;
    color: {c14};             /* Brighter cyan text */
    border: solid {c6};       /* Cyan border */
}}

Button.music-btn-main:focus {{
    background: transparent;
    color: {fg};              /* White text when focused */
    border: solid {c4};       /* Blue border highlight */
    text-style: bold;
}}

/* ========================================
   BUTTON STYLING - PLAY/PAUSE (CENTER)
   ======================================== */
Button.music-btn-play {{
    width: 5;
    height: 3;
    min-width: 5;
    max-width: 5;
    padding: 0 0;
    content-align: center middle;
    background: transparent;
    color: {c2};              /* Dark green text */
    border: solid {c8};       /* Dark gray border */
    margin-left: 1;
    margin-bottom: 1;
}}

Button.music-btn-play:hover {{
    background: transparent;
    color: {c10};             /* Bright green text on hover */
    border: solid {c2};       /* Green border */
    text-style: bold;
}}

Button.music-btn-play:focus {{
    background: transparent;
    color: {fg};              /* White text on focus */
    border: solid {c3};       /* Yellow border highlight */
    text-style: bold;
}}

/* ========================================
   SYSTEM INFO PANEL
   ======================================== */
.panel-system {{
    layout: vertical;
    align: center top;
    width: 100%;
    height: 100%;
    padding-top: 1;
    border: solid {c2};
}}

.system-title {{
    color: {c6};
    text-style: bold;
    margin-bottom: 1;
}}

#system-usage-bar {{
    color: {c3};
    text-align: center;
    width: auto;
    height: auto;
}}
"""

def get_file_mtime(config_path: str) -> float:
    """Get the modification time of a file."""
    try:
        return os.path.getmtime(config_path)
    except FileNotFoundError:
        return 0.0