#!/usr/bin/env python3
# Optimize: Use faster imports and caching

import os
import sys
import subprocess
import pickle
from configparser import ConfigParser
from pathlib import Path
from datetime import datetime

CACHE_FILE = Path.home() / ".cache/gell/apps.cache"

# Check for quick exit options first (before heavy imports)
if "--refresh" in sys.argv:
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    print("Cache cleared!")
    sys.exit(0)

# Now import Textual (this is the slow part)
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Input, Label, ListItem, ListView, Static
from textual.screen import Screen
from theme import generate_css, load_wal_colors

class DesktopEntry:
    """Represents a .desktop file entry"""
    def __init__(self, filepath):
        self.filepath = filepath
        self.name = ""
        self.exec_cmd = ""
        self.icon = ""
        self.terminal = False
        self.parse()
    
    def parse(self):
        """Parse the .desktop file"""
        config = ConfigParser(interpolation=None, strict=False)
        try:
            config.read(self.filepath, encoding='utf-8')
        except Exception:
            return
        
        if 'Desktop Entry' not in config:
            return
            
        entry = config['Desktop Entry']
        
        # Quick exit if hidden
        if entry.get('NoDisplay', 'false').lower() == 'true':
            return
        if entry.get('Hidden', 'false').lower() == 'true':
            return
            
        self.name = entry.get('Name', '')
        self.exec_cmd = entry.get('Exec', '')
        self.icon = entry.get('Icon', '')
        self.terminal = entry.get('Terminal', 'false').lower() == 'true'
    
    def launch(self):
        """Launch the application"""
        if not self.exec_cmd:
            return
        
        # Remove field codes
        cmd = self.exec_cmd
        for code in ['%f', '%F', '%u', '%U', '%d', '%D', '%n', '%N', '%i', '%c', '%k', '%v', '%m']:
            cmd = cmd.replace(code, '')
        
        try:
            if self.terminal:
                subprocess.Popen(cmd, shell=True, start_new_session=True)
            else:
                subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL, start_new_session=True)
        except Exception:
            pass

def fuzzy_match(query, text):
    """
    Fast fuzzy matching similar to fzf.
    Returns (matched, score) where higher score = better match.
    """
    if not query:
        return True, 0
    
    query = query.lower()
    text = text.lower()
    
    # Simple substring match gets high score
    if query in text:
        # Bonus if it's at the start
        if text.startswith(query):
            return True, 1000 + len(query)
        return True, 500 + len(query)
    
    # Fuzzy match: all chars must appear in order
    query_idx = 0
    score = 0
    consecutive = 0
    
    for i, char in enumerate(text):
        if query_idx < len(query) and char == query[query_idx]:
            query_idx += 1
            consecutive += 1
            # Bonus for consecutive matches
            score += 10 + consecutive * 2
        else:
            consecutive = 0
    
    if query_idx == len(query):
        return True, score
    
    return False, 0

def get_desktop_files():
    """Get all .desktop files from standard locations"""
    desktop_dirs = [
        Path.home() / ".local/share/applications",
        Path("/usr/share/applications"),
        Path("/usr/local/share/applications"),
    ]
    
    apps = []
    seen_names = set()
    
    for desktop_dir in desktop_dirs:
        if not desktop_dir.exists():
            continue
        
        for desktop_file in desktop_dir.glob("*.desktop"):
            try:
                entry = DesktopEntry(desktop_file)
                if entry.name and entry.name not in seen_names and entry.exec_cmd:
                    apps.append(entry)
                    seen_names.add(entry.name)
            except Exception:
                pass
    
    apps.sort(key=lambda x: x.name.lower())
    return apps

def get_desktop_files_cached():
    """Get desktop files with caching (1 hour)"""
    cache_time = 3600
    
    if CACHE_FILE.exists():
        cache_age = datetime.now().timestamp() - CACHE_FILE.stat().st_mtime
        if cache_age < cache_time:
            try:
                with open(CACHE_FILE, 'rb') as f:
                    return pickle.load(f)
            except Exception:
                pass
    
    apps = get_desktop_files()
    
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(apps, f)
    except Exception:
        pass
    
    return apps

class GellLauncher(Screen[None]):
    def compose(self) -> ComposeResult:
        with Vertical(id="gell-container"):
            with Container(id="Gell"):
                yield Static("Gell Launcher", classes="panel-content")
            with Container(id="Apps"):
                yield ListView(id="app-list")
            
            with Container(id="Input"):
                yield Input(
                    placeholder="Search apps...",
                    id="search-input"
                )
    
    def __init__(self):
        super().__init__()
        self.apps = get_desktop_files_cached()
        self.filtered_apps = self.apps.copy()

    def on_mount(self) -> None:
        """Set border titles after mounting"""
        self.query_one("#Gell").border_title = "Gell"
        self.update_app_list()
        self.query_one("#Input").border_title = "Input"
        
        # Focus the search input
        self.query_one("#search-input").focus()
    
    def on_screen_resume(self) -> None:
        """Called when screen becomes active again"""
        # Clear search input when window is shown again
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.filtered_apps = self.apps.copy()
        self.update_app_list()
        search_input.focus()
    
    def update_app_list(self):
        """Update the app list efficiently"""
        app_list = self.query_one("#app-list", ListView)
        app_list.clear()
        
        # Limit to first 100 for performance
        display_apps = self.filtered_apps[:100]
        
        for app in display_apps:
            app_list.append(ListItem(Label(app.name)))
        
        # Update count
        total = len(self.filtered_apps)
        displayed = len(display_apps)
        if total > displayed:
            self.query_one("#Apps").border_title = f"Apps ({displayed}/{total})"
        else:
            self.query_one("#Apps").border_title = f"Apps ({total})"
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter apps based on search input with fuzzy matching"""
        search_term = event.value
        
        if not search_term:
            self.filtered_apps = self.apps.copy()
        else:
            # Fuzzy match and score
            matches = []
            for app in self.apps:
                matched, score = fuzzy_match(search_term, app.name)
                if matched:
                    matches.append((app, score))
            
            # Sort by score (highest first)
            matches.sort(key=lambda x: x[1], reverse=True)
            self.filtered_apps = [app for app, score in matches]
        
        self.update_app_list()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Launch selected app"""
        index = event.list_view.index
        if index is not None and 0 <= index < len(self.filtered_apps):
            # Consider the 100 item limit
            display_limit = min(100, len(self.filtered_apps))
            if index < display_limit:
                app = self.filtered_apps[index]
                app.launch()
                # Clear input and hide window
                self.clear_and_hide()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Launch first app on Enter"""
        if self.filtered_apps:
            self.filtered_apps[0].launch()
            # Clear input and hide window
            self.clear_and_hide()
    
    def clear_and_hide(self):
        """Clear the search input and hide the window"""
        # Clear the search input first
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        self.filtered_apps = self.apps.copy()
        self.update_app_list()
        
        # Then hide the window
        try:
            # Move THIS window to special workspace
            subprocess.run(['hyprctl', 'dispatch', 'movetoworkspacesilent', 'special:gell'])
        except Exception:
            pass

class GellApp(App[None]):
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("escape", "hide_window", "Hide"),
        Binding("ctrl+c", "hide_window", "Hide"),
    ]
    
    def __init__(self):
        super().__init__()
        colors = load_wal_colors()
        self.CSS = generate_css(colors)
        self._disable_tooltips = True
    
    def on_mount(self) -> None:
        self.push_screen(GellLauncher())
    
    def action_hide_window(self) -> None:
        """Hide the window and clear search input"""
        # Get the current screen and clear input
        screen = self.screen
        if isinstance(screen, GellLauncher):
            screen.clear_and_hide()
        
        # Focus back to previous window
        try:
            subprocess.run(['hyprctl', 'dispatch', 'focuscurrentorlast'])
        except Exception:
            pass

if __name__ == "__main__":
    # Add --inline for kitty
    if "--inline" not in sys.argv:
        sys.argv.append("--inline")
    
    app = GellApp()
    app.run()