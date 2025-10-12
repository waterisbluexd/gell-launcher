"""
Launcher module: Handles the business logic and dynamic color reloading.
"""
from textual.app import ComposeResult
from UI import GellLauncherUI
from theme import load_wal_colors, generate_css, get_file_mtime


class GellLauncher(GellLauncherUI):  
    COLOR_CONFIG_PATH = '/home/wib/.cache/wal/colors-kitty.conf'
    _wal_colors = load_wal_colors(COLOR_CONFIG_PATH)
    DEFAULT_CSS = generate_css(_wal_colors)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_mtime = get_file_mtime(self.COLOR_CONFIG_PATH)
    
    def reload_colors(self) -> bool:
        current_mtime = get_file_mtime(self.COLOR_CONFIG_PATH)
        if current_mtime != self._last_mtime:
            # Reload colors
            type(self)._wal_colors = load_wal_colors(self.COLOR_CONFIG_PATH)
            self._last_mtime = current_mtime
            
            # Generate new CSS
            new_css = generate_css(type(self)._wal_colors)
            
            # Update the stylesheet
            self.app.stylesheet.reparse(new_css, scope=type(self).__name__)
            
            # Refresh the display
            self.refresh(layout=True)
            return True
        return False
    
    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Set up a timer to check for color changes every 2 seconds
        self.set_interval(2.0, self.reload_colors)