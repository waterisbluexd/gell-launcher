#!/usr/bin/env python3
"""
App launcher module - handles desktop file parsing, caching, and app list UI.
"""
import pickle
import subprocess
from pathlib import Path
from datetime import datetime
from configparser import ConfigParser

from textual.containers import Container
from textual.widgets import Input, Label, ListItem, ListView
from textual.app import ComposeResult

CACHE_FILE = Path.home() / ".cache/gell/apps.cache"


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
        config = ConfigParser(interpolation=None, strict=False)
        try:
            config.read(self.filepath, encoding='utf-8')
        except Exception:
            return
        
        if 'Desktop Entry' not in config:
            return
            
        entry = config['Desktop Entry']
        
        if entry.getboolean('NoDisplay', False) or entry.getboolean('Hidden', False):
            return
            
        self.name = entry.get('Name', '')
        self.exec_cmd = entry.get('Exec', '')
        self.icon = entry.get('Icon', '')
        self.terminal = entry.getboolean('Terminal', False)
    
    def launch(self):
        if not self.exec_cmd:
            return
        
        cmd = self.exec_cmd.split('%')[0].strip()
        
        try:
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
    Performs fuzzy matching on text with scoring.
    Returns (matched: bool, score: int)
    """
    if not query:
        return True, 0
    
    query = query.lower()
    text_lower = text.lower()
    
    if query in text_lower:
        score = 2000 - text_lower.find(query)
        return True, score
    
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
    """Scans system directories for .desktop files and returns parsed entries."""
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
    """Returns cached desktop files or refreshes cache if stale."""
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


def clear_cache():
    """Removes the app cache file."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()


class AppLauncherPanel:
    """Manages the app launcher UI components and logic."""
    
    def __init__(self, parent_screen):
        self.parent_screen = parent_screen
        self.apps = get_desktop_files_cached()
        self.filtered_apps = self.apps[:]
    
    def compose_list(self) -> ComposeResult:
        """Returns the app list container for middle panel."""
        yield ListView(id="app-list")
    
    def update_app_list(self):
        """Updates the ListView with filtered apps."""
        try:
            app_list = self.parent_screen.query_one("#app-list", ListView)
            app_list.clear()
            
            for app in self.filtered_apps[:100]:
                app_list.append(ListItem(Label(app.name)))
            
            middle_container = self.parent_screen.query_one("#Middle")
            current_title = middle_container.border_title or "Apps"
            base_title = current_title.split('(')[0].strip()
            middle_container.border_title = f"{base_title} ({len(self.filtered_apps)})"
        except Exception:
            pass
    
    def on_input_changed(self, value: str):
        """Filters apps based on search query."""
        if not value:
            self.filtered_apps = self.apps[:]
        else:
            matches = sorted(
                (app for app in self.apps if fuzzy_match(value, app.name)[0]),
                key=lambda app: fuzzy_match(value, app.name)[1],
                reverse=True
            )
            self.filtered_apps = matches
        self.update_app_list()
    
    def launch_selected_app(self, index: int) -> bool:
        """
        Launches the app at the given index.
        Returns True if app was launched successfully.
        """
        if self.filtered_apps and 0 <= index < len(self.filtered_apps):
            self.filtered_apps[index].launch()
            return True
        return False
    
    def get_selected_index(self) -> int:
        """Returns the currently selected app list index."""
        try:
            app_list = self.parent_screen.query_one("#app-list", ListView)
            return app_list.index if app_list.index is not None else 0
        except Exception:
            return 0
    
    def reset(self):
        """Resets the launcher to initial state."""
        try:
            search_input = self.parent_screen.query_one("#search-input", Input)
            search_input.value = ""
            search_input.focus()
        except Exception:
            pass
        self.filtered_apps = self.apps[:]
        self.update_app_list()