"""
Theme module: Handles pywal color loading and CSS generation.
"""
import os
from pathlib import Path

def load_wal_colors(config_path: str = '/home/wib/.cache/wal/colors-kitty.conf') -> dict[str, str]:
    """
    Parse pywal's kitty color config and return a dict of color names to hex values.
    """
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
    
    # Terminal colors (0-15)
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
/* Main container */
#gell-container {{
    width: 100%;
    height: 100%;
    max-width: 100;
    min-height: 25;
    padding_left: 1;
    padding_right: 1;
    background: {c0};
}}

/* Gell panel */
#Gell {{
    height: 30%;
    border: solid {c3};
    border-title-align: left;
    border-title-color: {c6};
    border-title-style: bold;
}}

/* Apps panel */
#Apps {{
    height: 64%;
    border: solid {c3};
    border-title-align: left;
    border-title-color: {c6};
    border-title-style: bold;
}}

/* App list view */
#app-list {{
    background: {c0};
    overflow-y: hidden;
    padding_left: 2;
    padding_right: 2;
}}
#app-list:focus {{
 background: transparent;
}}

/* Input panel */
#Input {{
    height: 6%;
    border: solid {c3};
    border-title-align: left;
    border-title-color: {c6};
    border-title-style: bold;
    
}}

.panel-content {{
    width: 100%;
    height: 100%;
}}

/* Search Input Styling */
#search-input {{
    width: 100%;
    border: none;
}}

#search-input:focus {{
}}

#search-input > .input--placeholder {{
    color: {c8};
    text-style: italic;
}}

#search-input > .input--cursor {{
    color: {c0};
    text-style: bold;
}}

/* Input content area */
Input {{
    background: transparent;
}}

Input:focus {{
    border: none;
}}
"""

def get_file_mtime(config_path: str) -> float:
    try:
        return os.path.getmtime(config_path)
    except FileNotFoundError:
        return 0.0