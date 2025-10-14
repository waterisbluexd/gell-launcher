#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Error: 'watchdog' is not installed. Please run 'pip install watchdog'.")
    sys.exit(1)

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Input, Static
from textual.screen import Screen
#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

# Imports for dynamic theme reloading
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Error: 'watchdog' is not installed. Please run 'pip install watchdog'.")
    sys.exit(1)

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Input, Static
from textual.screen import Screen

# Local imports
from theme import generate_css, load_wal_colors
from music_panel import MusicPanel
from dmenu import AppLauncherPanel, clear_cache
from system_panel import SystemPanel

# Handle cache refresh command
if "--refresh" in sys.argv:
    clear_cache()
    print("Cache cleared!")
    sys.exit(0)


class GellLauncher(Screen):
    """The main screen for the application launcher."""

    def __init__(self):
        super().__init__()
        self.app_launcher = AppLauncherPanel(self)
        self.music_panel = MusicPanel()
        self.system_panel = SystemPanel()
        
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
            yield from self.app_launcher.compose()
    
    def render_panel_launcher(self) -> ComposeResult:
        yield Static("Gell Launcher", classes="panel-content")

    def render_panel_music(self) -> ComposeResult:
        yield self.music_panel

    def render_panel_system(self) -> ComposeResult:
        yield self.system_panel

    def on_mount(self) -> None:
        self.update_panel_display()
        self.app_launcher.on_mount()
        self.start_panel_updates()
        
    def start_panel_updates(self):
        if self.system_update_timer:
            self.system_update_timer.stop()
        self.system_update_timer = self.set_interval(2.0, self.auto_update_panel)
    
    def auto_update_panel(self):
        if self.current_panel_index == 2:
            self.system_panel.refresh_info()
    
    def update_panel_display(self):
        panel_meta = self.panels[self.current_panel_index]
        panel_container = self.query_one("#Gell")
        
        panel_container.border_title = f"{panel_meta['name']} ({self.current_panel_index + 1}/{len(self.panels)})"
        
        panel_container.remove_children()
        panel_container.mount(*panel_meta['render']())

    def switch_panel(self, direction: int):
        self.current_panel_index = (self.current_panel_index + direction) % len(self.panels)
        self.update_panel_display()
        
        if self.panels[self.current_panel_index]['name'] == "Music Player":
            self.music_panel.on_panel_focus()
    
    def on_screen_resume(self) -> None:
        self.app_launcher.reset()
        self.current_panel_index = 0
        self.update_panel_display()
        self.start_panel_updates()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        self.app_launcher.on_input_changed(event.value)
    
    def on_list_view_selected(self, event) -> None:
        index = event.list_view.index
        if index is not None and self.app_launcher.launch_selected_app(index):
            self.parent.action_hide_window()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        index_to_launch = self.app_launcher.get_selected_index()
        if self.app_launcher.launch_selected_app(index_to_launch):
            self.parent.action_hide_window()

    def on_key(self, event) -> None:
        search_input = self.query_one("#search-input", Input)
        app_list = self.query_one("#app-list")

        if event.key == "down":
            if self.screen.focused is search_input:
                app_list.focus()
                app_list.index = 0 if app_list.index is None else app_list.index
            else:
                app_list.action_cursor_down()
            event.stop()
            return
        elif event.key == "up":
            if self.screen.focused is search_input:
                app_list.focus()
                app_list.index = len(app_list.children) - 1 if app_list.index is None else app_list.index
            else:
                app_list.action_cursor_up()
            event.stop()
            return

        if event.key == "shift+right":
            self.switch_panel(1)
            event.stop()
            return
        elif event.key == "shift+left":
            self.switch_panel(-1)
            event.stop()
            return

        if self.panels[self.current_panel_index]['name'] == "Music Player" and event.key == "space":
            self.music_panel.play_pause()
            event.stop()
            return

        if event.key == "escape":
            self.action_hide_window()
            event.stop()
            return

        if len(event.key) == 1 and event.key.isprintable():
            search_input.focus()
            search_input.value += event.key
            event.stop()

    def action_hide_window(self) -> None:
        try:
            subprocess.run(
                ['hyprctl', 'dispatch', 'togglespecialworkspace', 'gell'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            self.exit()

        if self.system_update_timer:
            self.system_update_timer.stop()

        self.app_launcher.reset()


class ThemeUpdateHandler(FileSystemEventHandler):
    """Watches for changes in the pywal colors file and triggers a theme reload."""
    def __init__(self, app_instance, file_to_watch):
        self.app = app_instance
        self.file_to_watch = str(file_to_watch)

    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.file_to_watch:
            self.app.call_from_thread(self.app.reload_theme)


class GellApp(App):
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("escape", "hide_window", "Hide", show=False),
        Binding("ctrl+c", "hide_window", "Hide", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.theme_observer = None
        self.wal_colors_path = Path.home() / ".cache/wal/colors-kitty.conf"
        self.reload_theme(is_initial_load=True)

    def reload_theme(self, is_initial_load: bool = False) -> None:
        """Loads wal colors, generates CSS, and applies it to the app."""
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
        except Exception as e:
            if is_initial_load:
                self.CSS = ""
            self.log(f"Error reloading theme: {e}")

    def start_theme_watcher(self) -> None:
        """Initializes and starts the watchdog observer in a background thread."""
        if not self.wal_colors_path.exists():
            self.log(f"Pywal theme file not found at {self.wal_colors_path}. Watcher not started.")
            return

        event_handler = ThemeUpdateHandler(self, self.wal_colors_path)
        self.theme_observer = Observer()
        self.theme_observer.schedule(event_handler, path=str(self.wal_colors_path.parent), recursive=False)
        
        self.theme_observer.daemon = True
        self.theme_observer.start()
        self.log(f"👀 Watching {self.wal_colors_path} for theme changes...")
    
    def on_mount(self) -> None:
        self.push_screen(GellLauncher())
        self.start_theme_watcher()
    
    def action_hide_window(self) -> None:
        screen = self.screen
        if isinstance(screen, GellLauncher):
            screen.action_hide_window()


if __name__ == "__main__":
    GellApp().run()
# Local imports
from theme import generate_css, load_wal_colors
from music_panel import MusicPanel
from dmenu import AppLauncherPanel, clear_cache
from system_panel import SystemPanel

# Handle cache refresh command
if "--refresh" in sys.argv:
    clear_cache()
    print("Cache cleared!")
    sys.exit(0)


class GellLauncher(Screen):
    """The main screen for the application launcher."""

    def __init__(self):
        super().__init__()
        self.app_launcher = AppLauncherPanel(self)
        self.music_panel = MusicPanel()
        self.system_panel = SystemPanel()
        
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
            yield from self.app_launcher.compose()
    
    def render_panel_launcher(self) -> ComposeResult:
        yield Static("Gell Launcher", classes="panel-content")

    def render_panel_music(self) -> ComposeResult:
        yield self.music_panel

    def render_panel_system(self) -> ComposeResult:
        yield self.system_panel

    def on_mount(self) -> None:
        self.update_panel_display()
        self.app_launcher.on_mount()
        self.start_panel_updates()
        
    def start_panel_updates(self):
        if self.system_update_timer:
            self.system_update_timer.stop()
        self.system_update_timer = self.set_interval(2.0, self.auto_update_panel)
    
    def auto_update_panel(self):
        if self.current_panel_index == 2:
            self.system_panel.refresh_info()
    
    def update_panel_display(self):
        panel_meta = self.panels[self.current_panel_index]
        panel_container = self.query_one("#Gell")
        
        panel_container.border_title = f"{panel_meta['name']} ({self.current_panel_index + 1}/{len(self.panels)})"
        
        panel_container.remove_children()
        panel_container.mount(*panel_meta['render']())

    def switch_panel(self, direction: int):
        self.current_panel_index = (self.current_panel_index + direction) % len(self.panels)
        self.update_panel_display()
        
        if self.panels[self.current_panel_index]['name'] == "Music Player":
            self.music_panel.on_panel_focus()
    
    def on_screen_resume(self) -> None:
        self.app_launcher.reset()
        self.current_panel_index = 0
        self.update_panel_display()
        self.start_panel_updates()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        self.app_launcher.on_input_changed(event.value)
    
    def on_list_view_selected(self, event) -> None:
        index = event.list_view.index
        if index is not None and self.app_launcher.launch_selected_app(index):
            self.parent.action_hide_window()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        index_to_launch = self.app_launcher.get_selected_index()
        if self.app_launcher.launch_selected_app(index_to_launch):
            self.parent.action_hide_window()

    def on_key(self, event) -> None:
        search_input = self.query_one("#search-input", Input)
        app_list = self.query_one("#app-list")

        if event.key == "down":
            if self.screen.focused is search_input:
                app_list.focus()
                app_list.index = 0 if app_list.index is None else app_list.index
            else:
                app_list.action_cursor_down()
            event.stop()
            return
        elif event.key == "up":
            if self.screen.focused is search_input:
                app_list.focus()
                app_list.index = len(app_list.children) - 1 if app_list.index is None else app_list.index
            else:
                app_list.action_cursor_up()
            event.stop()
            return

        if event.key == "shift+right":
            self.switch_panel(1)
            event.stop()
            return
        elif event.key == "shift+left":
            self.switch_panel(-1)
            event.stop()
            return

        if self.panels[self.current_panel_index]['name'] == "Music Player" and event.key == "space":
            self.music_panel.play_pause()
            event.stop()
            return

        if event.key == "escape":
            self.action_hide_window()
            event.stop()
            return

        if len(event.key) == 1 and event.key.isprintable():
            search_input.focus()
            search_input.value += event.key
            event.stop()

    def action_hide_window(self) -> None:
        try:
            subprocess.run(
                ['hyprctl', 'dispatch', 'togglespecialworkspace', 'gell'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            self.exit()

        if self.system_update_timer:
            self.system_update_timer.stop()

        self.app_launcher.reset()


class ThemeUpdateHandler(FileSystemEventHandler):
    """Watches for changes in the pywal colors file and triggers a theme reload."""
    def __init__(self, app_instance, file_to_watch):
        self.app = app_instance
        self.file_to_watch = str(file_to_watch)

    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.file_to_watch:
            self.app.call_from_thread(self.app.reload_theme)


class GellApp(App):
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("escape", "hide_window", "Hide", show=False),
        Binding("ctrl+c", "hide_window", "Hide", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.theme_observer = None
        self.wal_colors_path = Path.home() / ".cache/wal/colors-kitty.conf"
        self.reload_theme(is_initial_load=True)

    def reload_theme(self, is_initial_load: bool = False) -> None:
        """Loads wal colors, generates CSS, and applies it to the app."""
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
        except Exception as e:
            if is_initial_load:
                self.CSS = ""
            self.log(f"Error reloading theme: {e}")

    def start_theme_watcher(self) -> None:
        """Initializes and starts the watchdog observer in a background thread."""
        if not self.wal_colors_path.exists():
            self.log(f"Pywal theme file not found at {self.wal_colors_path}. Watcher not started.")
            return

        event_handler = ThemeUpdateHandler(self, self.wal_colors_path)
        self.theme_observer = Observer()
        self.theme_observer.schedule(event_handler, path=str(self.wal_colors_path.parent), recursive=False)
        
        self.theme_observer.daemon = True
        self.theme_observer.start()
        self.log(f"👀 Watching {self.wal_colors_path} for theme changes...")
    
    def on_mount(self) -> None:
        self.push_screen(GellLauncher())
        self.start_theme_watcher()
    
    def action_hide_window(self) -> None:
        screen = self.screen
        if isinstance(screen, GellLauncher):
            screen.action_hide_window()


if __name__ == "__main__":
    GellApp().run()