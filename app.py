#!/usr/bin/env python3
"""
Gell Launcher - A Textual-based application launcher with multiple panels
"""
import sys
import subprocess
from pathlib import Path
from typing import Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Error: 'watchdog' is not installed. Please run 'pip install watchdog'.")
    sys.exit(1)

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Input
from textual.screen import Screen

# Local imports
from theme import generate_css, load_wal_colors
from music_panel import MusicPanel
from dmenu import AppLauncherPanel, clear_cache
from system_panel import SystemPanel
from gell_panel import GellPanel
from weather_panel import WeatherPanel
from services_panel import ServicesPanel
from clipboard import ClipboardPanel


# Handle cache refresh command
if "--refresh" in sys.argv:
    clear_cache()
    print("Cache cleared!")
    sys.exit(0)


class GellLauncher(Screen):
    """The main screen for the application launcher."""

    def __init__(self):
        super().__init__()
        
        # Initialize panels
        self.app_launcher = AppLauncherPanel(self)
        self.music_panel = MusicPanel()
        self.system_panel = SystemPanel()
        self.gell_panel = GellPanel()
        self.weather_panel = WeatherPanel()
        self.services_panel = ServicesPanel()
        self.clipboard_panel = ClipboardPanel()  # Now it's a widget!
        
        # Panel configuration for top panel (Gell)
        self.top_panels = [
            {"name": "Gell Launcher", "render": self.render_panel_launcher},
            {"name": "Weather", "render": self.render_panel_weather},
            {"name": "Music Player", "render": self.render_panel_music},
            {"name": "Services", "render": self.render_panel_services},
            {"name": "System Info", "render": self.render_panel_system},
        ]
        
        # Middle panels configuration (Apps/Clipboard area)
        self.middle_panels = [
            {"name": "Apps", "render": self.render_middle_apps},
            {"name": "Clipboard", "render": self.render_middle_clipboard},
        ]
        
        self.current_top_panel_index = 0
        self.current_middle_panel_index = 0
        self.prewarm_mode = "--prewarm" in sys.argv

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        with Vertical(id="gell-container"):
            yield Container(id="Gell")
            yield Container(id="Middle")
            yield Container(id="Input")
            yield Input(placeholder="Search apps...", id="search-input")
    
    def render_panel_launcher(self) -> ComposeResult:
        """Render the Gell launcher panel."""
        yield self.gell_panel

    def render_panel_weather(self) -> ComposeResult:
        """Render the weather panel."""
        yield self.weather_panel

    def render_panel_music(self) -> ComposeResult:
        """Render the music player panel."""
        yield self.music_panel
        
    def render_panel_services(self) -> ComposeResult:
        """Render the services panel."""
        yield self.services_panel

    def render_panel_system(self) -> ComposeResult:
        """Render the system info panel."""
        yield self.system_panel
    
    def render_middle_apps(self) -> ComposeResult:
        """Render the apps list in middle panel."""
        yield from self.app_launcher.compose_list()
    
    def render_middle_clipboard(self) -> ComposeResult:
        """Render the clipboard panel in middle area."""
        # Simply yield the ClipboardPanel widget
        # It will handle its own composition via its compose() method
        yield self.clipboard_panel

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Start the clock early - needs to be done after app is available
        if hasattr(self, 'app') and self.app:
            self.gell_panel.start_clock_early(self.app)
        
        if self.prewarm_mode:
            self.set_timer(0.1, self.prewarm_all_panels)
        else:
            self._initialize_display()

    def _initialize_display(self) -> None:
        """Initialize the display and focus the search input."""
        self.update_top_panel_display()
        self.update_middle_panel_display()
        
        # Set up Input container border
        try:
            input_container = self.query_one("#Input")
            input_container.border_title = "Input"
        except Exception:
            pass
        
        try:
            search_input = self.query_one("#search-input", Input)
            search_input.focus()
        except Exception as e:
            self.app.log(f"Failed to focus search input: {e}")

    def hide_window_immediately(self) -> None:
        """Move the window to the special workspace without animation."""
        try:
            subprocess.run(
                ['hyprctl', 'dispatch', 'movetoworkspacesilent', 'special:gell'],
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                check=False
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
    
    def prewarm_all_panels(self) -> None:
        """
        Initialize the app and hide the window immediately.
        The clock is already running thanks to start_clock_early().
        """
        self.current_top_panel_index = 0
        self.current_middle_panel_index = 0
        self.update_top_panel_display()
        self.update_middle_panel_display()
        
        # Set up Input container border
        try:
            input_container = self.query_one("#Input")
            input_container.border_title = "Input"
        except Exception:
            pass
        
        # Hide the window quickly
        self.set_timer(0.05, self.hide_window_immediately)
        
        # Pre-warming is complete
        self.prewarm_mode = False
        
    def update_top_panel_display(self) -> None:
        """Update the display to show the current top panel."""
        panel_meta = self.top_panels[self.current_top_panel_index]
        
        try:
            panel_container = self.query_one("#Gell")
            panel_container.border_title = (
                f"{panel_meta['name']} "
                f"({self.current_top_panel_index + 1}/{len(self.top_panels)})"
            )
            
            panel_container.remove_children()
            panel_container.mount(*panel_meta['render']())
        except Exception as e:
            self.app.log(f"Error updating top panel display: {e}")
    
    def update_middle_panel_display(self) -> None:
        """Update the display to show the current middle panel."""
        panel_meta = self.middle_panels[self.current_middle_panel_index]
        
        try:
            middle_container = self.query_one("#Middle")
            middle_container.border_title = (
                f"{panel_meta['name']} "
                f"({self.current_middle_panel_index + 1}/{len(self.middle_panels)})"
            )
            
            middle_container.remove_children()
            middle_container.mount(*panel_meta['render']())
            
            # Call setup for specific panels
            if panel_meta['name'] == "Apps":
                self.app_launcher.update_app_list()
            elif panel_meta['name'] == "Clipboard":
                # Refresh the clipboard panel to show latest history
                self.clipboard_panel.refresh_display()
                
        except Exception as e:
            self.app.log(f"Error updating middle panel display: {e}")

    def switch_top_panel(self, direction: int) -> None:
        """Switch to the next/previous top panel."""
        self.current_top_panel_index = (
            (self.current_top_panel_index + direction) % len(self.top_panels)
        )
        self.update_top_panel_display()
        
        # Notify panels when they receive focus
        panel_name = self.top_panels[self.current_top_panel_index]['name']
        if panel_name == "Music Player":
            self.music_panel.on_panel_focus()
        elif panel_name == "Gell Launcher":
            self.gell_panel.on_panel_focus()
    
    def switch_middle_panel(self, direction: int) -> None:
        """Switch to the next/previous middle panel."""
        self.current_middle_panel_index = (
            (self.current_middle_panel_index + direction) % len(self.middle_panels)
        )
        self.update_middle_panel_display()
        
        # Focus appropriate widget based on panel
        panel_name = self.middle_panels[self.current_middle_panel_index]['name']
        if panel_name == "Apps":
            try:
                search_input = self.query_one("#search-input", Input)
                search_input.focus()
            except Exception:
                pass
    
    def on_screen_resume(self) -> None:
        """Called when the screen is resumed."""
        self.app_launcher.reset()
        
        # Reset to first panels
        if self.current_top_panel_index != 0:
            self.current_top_panel_index = 0
            self.update_top_panel_display()
        
        if self.current_middle_panel_index != 0:
            self.current_middle_panel_index = 0
            self.update_middle_panel_display()
        
        # Focus the search input
        try:
            search_input = self.query_one("#search-input", Input)
            search_input.focus()
        except Exception as e:
            self.app.log(f"Failed to focus search input on resume: {e}")
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        self.app_launcher.on_input_changed(event.value)
    
    def on_list_view_selected(self, event) -> None:
        """Handle app selection from the list."""
        index = event.list_view.index
        if index is not None and self.app_launcher.launch_selected_app(index):
            self.action_hide_window()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission."""
        index_to_launch = self.app_launcher.get_selected_index()
        if self.app_launcher.launch_selected_app(index_to_launch):
            self.action_hide_window()
    
    def on_button_pressed(self, event) -> None:
        """Handle button presses from various panels."""
        button_id = event.button.id or ""
        
        # Handle clipboard buttons
        if button_id.startswith("clip-btn-"):
            try:
                idx = int(button_id.split("-")[-1])
                if 0 <= idx < len(self.clipboard_panel.history):
                    self.clipboard_panel.set_clipboard(self.clipboard_panel.history[idx])
                    # Hide window after copying
                    self.action_hide_window()
            except (ValueError, IndexError):
                pass
            event.stop()

    def on_key(self, event) -> None:
        """Handle keyboard input."""
        # Block input during prewarm mode
        if self.prewarm_mode:
            event.stop()
            return
        
        # Get current focus
        try:
            search_input = self.query_one("#search-input", Input)
        except Exception:
            search_input = None
        
        focused_widget = self.focused
        
        # Handle middle panel switching (up/down for Apps/Clipboard)
        if event.key == "shift+down":
            self.switch_middle_panel(1)
            event.stop()
            return
            
        elif event.key == "shift+up":
            self.switch_middle_panel(-1)
            event.stop()
            return

        # Handle top panel switching (left/right)
        if event.key == "shift+right":
            self.switch_top_panel(1)
            event.stop()
            return
            
        elif event.key == "shift+left":
            self.switch_top_panel(-1)
            event.stop()
            return
        
        # Only handle app list navigation when Apps panel is active
        if self.current_middle_panel_index == 0:  # Apps panel
            try:
                app_list = self.query_one("#app-list")
            except Exception:
                app_list = None
            
            # Handle up/down navigation in app list
            if event.key == "down" and app_list:
                if focused_widget is search_input:
                    app_list.focus()
                    if app_list.index is None:
                        app_list.index = 0
                else:
                    app_list.action_cursor_down()
                event.stop()
                return
                
            elif event.key == "up" and app_list:
                if focused_widget is search_input:
                    app_list.focus()
                    if app_list.index is None:
                        app_list.index = len(app_list.children) - 1
                else:
                    app_list.action_cursor_up()
                event.stop()
                return

        # Handle music player controls
        current_top_panel = self.top_panels[self.current_top_panel_index]['name']
        if current_top_panel == "Music Player" and event.key == "space":
            self.music_panel.play_pause()
            event.stop()
            return

        # Handle escape key
        if event.key == "escape":
            self.action_hide_window()
            event.stop()
            return

        # Focus search input on printable character (only in Apps panel)
        if (self.current_middle_panel_index == 0 and 
            search_input and
            focused_widget is not search_input and 
            event.key.isprintable() and 
            len(event.key) == 1):
            search_input.focus()

    def action_hide_window(self) -> None:
        """Hide the launcher window."""
        try:
            subprocess.run(
                ['hyprctl', 'dispatch', 'togglespecialworkspace', 'gell'],
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                check=False
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            self.app.exit()
        
        self.app_launcher.reset()


class ThemeUpdateHandler(FileSystemEventHandler):
    """Watches for changes in the pywal colors file and triggers a theme reload."""
    
    def __init__(self, app_instance: 'GellApp', file_to_watch: Path):
        super().__init__()
        self.app = app_instance
        self.file_to_watch = str(file_to_watch)

    def on_modified(self, event) -> None:
        """Called when the watched file is modified."""
        if not event.is_directory and event.src_path == self.file_to_watch:
            self.app.call_from_thread(self.app.reload_theme)


class GellApp(App):
    """Main application class for Gell Launcher."""
    
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("escape", "hide_window", "Hide", show=False),
        Binding("ctrl+c", "hide_window", "Hide", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.theme_observer: Optional[Observer] = None
        self.wal_colors_path = Path.home() / ".cache/wal/colors-kitty.conf"
        self.reload_theme(is_initial_load=True)

    def reload_theme(self, is_initial_load: bool = False) -> None:
        """Load wal colors, generate CSS, and apply it to the app."""
        try:
            colors = load_wal_colors(str(self.wal_colors_path))
            new_css = generate_css(colors)
            
            if is_initial_load:
                self.CSS = new_css
            else:
                self.stylesheet.clear()
                self.stylesheet.read_string(new_css)
                self.refresh_css(update_instances=True)
                self.log("🎨 Theme reloaded successfully from pywal.")
                
        except FileNotFoundError:
            self.log(f"Theme file not found: {self.wal_colors_path}")
            if is_initial_load:
                self.CSS = ""
        except Exception as e:
            self.log(f"Error reloading theme: {e}")
            if is_initial_load:
                self.CSS = ""

    def start_theme_watcher(self) -> None:
        """Initialize and start the watchdog observer in a background thread."""
        if not self.wal_colors_path.exists():
            self.log(
                f"Pywal theme file not found at {self.wal_colors_path}. "
                "Watcher not started."
            )
            return

        try:
            event_handler = ThemeUpdateHandler(self, self.wal_colors_path)
            self.theme_observer = Observer()
            self.theme_observer.schedule(
                event_handler, 
                path=str(self.wal_colors_path.parent), 
                recursive=False
            )
            
            self.theme_observer.daemon = True
            self.theme_observer.start()
            self.log(f"👀 Watching {self.wal_colors_path} for theme changes...")
        except Exception as e:
            self.log(f"Failed to start theme watcher: {e}")
    
    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.push_screen(GellLauncher())
        self.start_theme_watcher()
    
    def action_hide_window(self) -> None:
        """Action to hide the window."""
        screen = self.screen
        if isinstance(screen, GellLauncher):
            screen.action_hide_window()


if __name__ == "__main__":
    GellApp().run()