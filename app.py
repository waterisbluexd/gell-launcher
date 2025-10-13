#!/usr/bin/env python3
import os
import sys
import subprocess
import pickle
from configparser import ConfigParser
from pathlib import Path
from datetime import datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Input, Label, ListItem, ListView, Static
from textual.screen import Screen

# Local imports
from theme import generate_css, load_wal_colors
from music_panel import MusicPanel  # Import the refactored music panel

CACHE_FILE = Path.home() / ".cache/gell/apps.cache"

# Handle command-line arguments before heavy imports
if "--refresh" in sys.argv:
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    print("Cache cleared!")
    sys.exit(0)

class DesktopEntry:
    """Represents and parses a .desktop file entry."""
    def __init__(self, filepath):
        self.filepath = filepath
        self.name = ""
        self.exec_cmd = ""
        self.icon = ""
        self.terminal = False
        self._parse()
    
    def _parse(self):
        """Parse the .desktop file contents."""
        config = ConfigParser(interpolation=None, strict=False)
        try:
            config.read(self.filepath, encoding='utf-8')
        except Exception:
            return
        
        if 'Desktop Entry' not in config:
            return
            
        entry = config['Desktop Entry']
        
        if entry.getboolean('NoDisplay') or entry.getboolean('Hidden'):
            return
            
        self.name = entry.get('Name', '')
        self.exec_cmd = entry.get('Exec', '')
        self.icon = entry.get('Icon', '')
        self.terminal = entry.getboolean('Terminal')
    
    def launch(self):
        """Launch the application, cleaning the exec command first."""
        if not self.exec_cmd:
            return
        
        # Remove field codes like %f, %U, etc.
        cmd = self.exec_cmd.split('%')[0].strip()
        
        try:
            # Use Popen with start_new_session to detach the process
            subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL, 
                start_new_session=True
            )
        except Exception:
            pass

def fuzzy_match(query: str, text: str) -> tuple[bool, int]:
    """
    A simple and fast fuzzy matching algorithm.
    Returns (True, score) if it's a match, otherwise (False, 0).
    """
    if not query:
        return True, 0
    
    query = query.lower()
    text_lower = text.lower()
    
    # Prioritize exact substring matches
    if query in text_lower:
        score = 2000 - text_lower.find(query)  # Higher score for earlier matches
        return True, score
    
    # Perform fuzzy character matching
    query_idx, score, consecutive = 0, 0, 0
    for char in text_lower:
        if query_idx < len(query) and char == query[query_idx]:
            query_idx += 1
            consecutive += 1
            score += 10 + consecutive * 5
        else:
            consecutive = 0
    
    return (query_idx == len(query)), score

def get_desktop_files() -> list[DesktopEntry]:
    """Scan standard locations for all .desktop files."""
    desktop_dirs = [
        Path.home() / ".local/share/applications",
        Path("/usr/share/applications"),
        Path("/usr/local/share/applications"),
    ]
    
    apps, seen_names = [], set()
    for desktop_dir in desktop_dirs:
        if not desktop_dir.exists():
            continue
        for desktop_file in desktop_dir.glob("*.desktop"):
            try:
                entry = DesktopEntry(desktop_file)
                if entry.name and entry.exec_cmd and entry.name not in seen_names:
                    apps.append(entry)
                    seen_names.add(entry.name)
            except Exception:
                pass
    
    apps.sort(key=lambda x: x.name.lower())
    return apps

def get_desktop_files_cached() -> list[DesktopEntry]:
    """Get desktop files, using a cache if it's recent."""
    if CACHE_FILE.exists():
        try:
            if (datetime.now().timestamp() - CACHE_FILE.stat().st_mtime) < 3600:
                with CACHE_FILE.open('rb') as f:
                    return pickle.load(f)
        except Exception:
            pass
    
    apps = get_desktop_files()
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CACHE_FILE.open('wb') as f:
            pickle.dump(apps, f)
    except Exception:
        pass
    
    return apps

def get_system_info() -> dict:
    """Get basic system information like uptime and memory usage."""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_h, rem = divmod(uptime_seconds, 3600)
            uptime_m, _ = divmod(rem, 60)
            uptime = f"{int(uptime_h)}h {int(uptime_m)}m"

        with open('/proc/meminfo', 'r') as f:
            meminfo = {line.split(':')[0]: line.split(':')[1].strip() for line in f}
        
        mem_total_kb = int(meminfo['MemTotal'].split()[0])
        mem_available_kb = int(meminfo['MemAvailable'].split()[0])
        mem_used_mb = (mem_total_kb - mem_available_kb) // 1024
        mem_total_mb = mem_total_kb // 1024
        mem_percent = int((mem_used_mb / mem_total_mb) * 100) if mem_total_mb > 0 else 0
        
        return {
            'uptime': uptime,
            'mem_used': mem_used_mb,
            'mem_total': mem_total_mb,
            'mem_percent': mem_percent
        }
    except (FileNotFoundError, KeyError, ValueError):
        return {'uptime': 'N/A', 'mem_used': 0, 'mem_total': 0, 'mem_percent': 0}

class GellLauncher(Screen):
    """The main screen for the application launcher."""

    def __init__(self):
        super().__init__()
        self.apps = get_desktop_files_cached()
        self.filtered_apps = self.apps[:]
        
        # The MusicPanel widget is now a self-contained component
        self.music_panel = MusicPanel()
        
        self.panels = [
            {"name": "Gell Launcher", "render": self.render_panel_launcher},
            {"name": "Music Player", "render": self.render_panel_music},
            {"name": "System Info", "render": self.render_panel_system},
        ]
        self.current_panel_index = 0
        self.system_update_timer = None

    def compose(self) -> ComposeResult:
        with Vertical(id="gell-container"):
            yield Container(id="Gell")
            with Container(id="Apps"):
                yield ListView(id="app-list")
            with Container(id="Input"):
                yield Input(placeholder="Search apps...", id="search-input")
    
    def render_panel_launcher(self) -> ComposeResult:
        """Render the default Gell Launcher panel."""
        yield Static("Gell Launcher", classes="panel-content")

    def render_panel_music(self) -> ComposeResult:
        """Render the Music Player panel by yielding the widget instance."""
        yield self.music_panel

    def render_panel_system(self) -> ComposeResult:
        """Render the System Info panel with current stats."""
        info = get_system_info()
        yield Static("System Status", classes="system-title")
        bar = "█" * (info['mem_percent'] // 10) + "░" * (10 - info['mem_percent'] // 10)
        yield Static(f"Uptime: {info['uptime']:>12}", classes="stat-row")
        yield Static(f"Memory: {info['mem_used']}MB / {info['mem_total']}MB", classes="stat-row")
        yield Static(f"Usage:  {bar} {info['mem_percent']}%", classes="stat-row")

    def on_mount(self) -> None:
        self.update_panel_display()
        self.update_app_list()
        self.query_one("#Input").border_title = "Input"
        self.query_one("#search-input").focus()
        self.start_panel_updates()
        
    def start_panel_updates(self):
        """Start a timer to update the system info panel."""
        if self.system_update_timer:
            self.system_update_timer.stop()
        self.system_update_timer = self.set_interval(2.0, self.auto_update_panel)
    
    def auto_update_panel(self):
        """Automatically re-render the current panel if it's the system panel."""
        if self.current_panel_index == 2: # Only for System Info panel
            self.update_panel_display()
    
    def update_panel_display(self):
        """Update the panel content and border title."""
        panel_meta = self.panels[self.current_panel_index]
        panel_container = self.query_one("#Gell")
        
        panel_container.border_title = f"{panel_meta['name']} ({self.current_panel_index + 1}/{len(self.panels)})"
        
        # Re-render the panel by mounting its content
        panel_container.remove_children()
        panel_container.mount(*panel_meta['render']())

    def switch_panel(self, direction: int):
        """Switch to the next or previous panel."""
        self.current_panel_index = (self.current_panel_index + direction) % len(self.panels)
        self.update_panel_display()
    
    def on_screen_resume(self) -> None:
        """Called when the screen becomes active again."""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        search_input.focus()
        self.filtered_apps = self.apps[:]
        self.update_app_list()
        self.current_panel_index = 0
        self.update_panel_display()
        self.start_panel_updates()
    
    def update_app_list(self):
        """Update the app list based on the current filter."""
        app_list = self.query_one("#app-list", ListView)
        app_list.clear()
        
        # Limit display to the first 100 results for performance
        for app in self.filtered_apps[:100]:
            app_list.append(ListItem(Label(app.name)))
        
        self.query_one("#Apps").border_title = f"Apps ({len(self.filtered_apps)})"
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter apps with fuzzy matching as the user types."""
        if not event.value:
            self.filtered_apps = self.apps[:]
        else:
            matches = sorted(
                (app for app in self.apps if fuzzy_match(event.value, app.name)[0]),
                key=lambda app: fuzzy_match(event.value, app.name)[1],
                reverse=True
            )
            self.filtered_apps = matches
        self.update_app_list()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Launch the selected app and hide the window."""
        index = event.list_view.index
        if index is not None and 0 <= index < len(self.filtered_apps):
            self.filtered_apps[index].launch()
            self.parent.action_hide_window()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Launch the top or highlighted app on Enter."""
        app_list = self.query_one("#app-list", ListView)
        index_to_launch = app_list.index if app_list.index is not None else 0

        if self.filtered_apps and 0 <= index_to_launch < len(self.filtered_apps):
            self.filtered_apps[index_to_launch].launch()
            self.parent.action_hide_window()

    def on_key(self, event) -> None:
        """Handle global key presses for panel switching and app list navigation."""
        if event.key == "shift+right":
            self.switch_panel(1)
            event.stop()
        elif event.key == "shift+left":
            self.switch_panel(-1)
            event.stop()
        
        # Delegate music controls to the MusicPanel widget when it's active
        elif self.current_panel_index == 1:
            if event.key == "space":
                self.music_panel.play_pause()
            else:
                return # Don't stop event if it's not a music control key
            event.stop()
        
        # App list navigation
        elif event.key in ("up", "down"):
            app_list = self.query_one("#app-list", ListView)
            if app_list.index is None: app_list.index = 0
            app_list.action_cursor_down() if event.key == "down" else app_list.action_cursor_up()
            event.stop()

class GellApp(App):
    """The main Textual application class."""
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("escape", "hide_window", "Hide", show=False),
        Binding("ctrl+c", "hide_window", "Hide", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.CSS = generate_css(load_wal_colors())
    
    def on_mount(self) -> None:
        self.push_screen(GellLauncher())
    
    def action_hide_window(self) -> None:
        """Hide the window and reset its state."""
        screen = self.screen
        if isinstance(screen, GellLauncher):
            # Stop timers to save resources when hidden
            if screen.system_update_timer:
                screen.system_update_timer.stop()
            # Toggle the special workspace to hide the window
            try:
                subprocess.run(['hyprctl', 'dispatch', 'togglespecialworkspace', 'gell'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                pass # hyprctl not available, just exit
                self.exit()

if __name__ == "__main__":
    if "--inline" not in sys.argv:
        sys.argv.append("--inline")
    GellApp().run()

