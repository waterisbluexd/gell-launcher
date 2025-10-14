import subprocess
import time
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widget import Widget
from textual.widgets import Static, Button
from textual.reactive import reactive
# FIX: Corrected the import path for the NoMatches exception.
from textual.css.query import NoMatches

def get_playerctl_metadata():
    """
    Fetch current media info from playerctl.
    Returns a dictionary with track info or None if nothing is playing.
    """
    try:
        result = subprocess.run(
            ['playerctl', '-l'], capture_output=True, text=True, timeout=1
        )
        if not result.stdout.strip():
            return None

        format_str = (
            '{{title}}\n{{artist}}\n{{album}}\n{{status}}\n'
            '{{position}}\n{{mpris:length}}\n{{mpris:artUrl}}\n{{playerName}}'
        )
        result = subprocess.run(
            ['playerctl', 'metadata', '--format', format_str],
            capture_output=True, text=True, timeout=1
        )
        
        if result.returncode != 0:
            return None

        lines = result.stdout.strip().split('\n')
        if len(lines) < 8:
            return None
            
        (title, artist, album, status, position_str, length_micro, art_url, player) = lines[:8]
        
        metadata = {
            'title': title or "Unknown Track",
            'artist': artist or "Unknown Artist",
            'album': album or "",
            'status': status or "Stopped",
            'player': player or "Unknown"
        }

        try:
            position_microseconds = int(float(position_str))
            metadata['position'] = position_microseconds // 1000000
        except (ValueError, TypeError):
            metadata['position'] = 0
            
        try:
            metadata['length'] = int(length_micro) // 1000000
        except (ValueError, TypeError):
            metadata['length'] = 0

        if art_url.startswith('file://'):
            metadata['art_path'] = art_url[7:]
        else:
            metadata['art_path'] = None
            
        return metadata
        
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return None


def format_time(seconds: int) -> str:
    """Convert seconds to a standard MM:SS format."""
    if seconds < 0:
        return "0:00"
    mins, secs = divmod(int(seconds), 60)
    return f"{mins}:{secs:02d}"


def create_progress_bar(position: int, length: int, width: int = 30) -> str:
    """
    Create a text-based progress bar string.
    """
    if length <= 0:
        return "[" + "─" * width + "]"
    
    progress = min(position / length, 1.0)
    filled = int(progress * (width - 1))
    
    bar = "━" * filled + "●" + "─" * (width - filled - 1)
    return f"[{bar}]"


class MusicPanel(Widget):
    """A self-contained, self-updating widget for music player controls."""
    
    current_position = reactive(0)

    def __init__(self):
        super().__init__()
        self.last_metadata = None
        self.last_fetch_time = 0
        self.is_playing = False

    def on_mount(self) -> None:
        """Start timers: fast UI updates + periodic metadata sync."""
        self.display_timer = self.set_interval(0.5, self.update_display_position)
        self.fetch_timer = self.set_interval(3.0, self.fetch_metadata)
        self.fetch_metadata()

    def on_panel_focus(self) -> None:
        """Force a metadata fetch when the panel becomes active."""
        self.fetch_metadata()
    
    def fetch_metadata(self) -> None:
        """Fetch fresh metadata from playerctl and sync local state."""
        metadata = get_playerctl_metadata()
        
        if metadata:
            last_title = self.last_metadata['title'] if self.last_metadata else None
            last_artist = self.last_metadata['artist'] if self.last_metadata else None
            last_length = self.last_metadata['length'] if self.last_metadata else None

            track_changed = (
                self.last_metadata is None or
                metadata['title'] != last_title or
                metadata['artist'] != last_artist or
                metadata['length'] != last_length
            )
            
            play_state_changed = self.last_metadata and (metadata['status'] == 'Playing') != self.is_playing
            
            self.last_metadata = metadata
            self.is_playing = (metadata['status'] == 'Playing')
            self.last_fetch_time = time.time()
            
            if track_changed:
                self.current_position = metadata['position']
                self.recompose()
            elif play_state_changed:
                self.update_play_button()
        else:
            if self.last_metadata is not None:
                self.last_metadata = None
                self.recompose()
    
    def update_display_position(self) -> None:
        """Update current position calculation for the display."""
        if not self.last_metadata:
            return
        
        if self.is_playing:
            elapsed = time.time() - self.last_fetch_time
            new_position = int(self.last_metadata['position'] + elapsed)
            
            if new_position <= self.last_metadata['length']:
                self.current_position = new_position
            else:
                self.current_position = self.last_metadata['length']
        else:
            self.current_position = int(self.last_metadata['position'])
    
    def watch_current_position(self, new_position: int) -> None:
        """Called when current_position changes - update the display widgets."""
        if not self.last_metadata:
            return
        
        try:
            current_time = format_time(new_position)
            progress_bar = create_progress_bar(new_position, self.last_metadata['length'], width=25)
            
            time_widget = self.query_one("#current-time", Static)
            progress_widget = self.query_one("#progress-bar", Static)
            
            time_widget.update(current_time)
            progress_widget.update(progress_bar)
        except NoMatches:
            pass
    
    def update_play_button(self) -> None:
        """Update just the play/pause button icon."""
        try:
            play_icon = "▶" if not self.is_playing else "⏸"
            play_button = self.query_one("#btn-play", Button)
            play_button.label = play_icon
        except NoMatches:
            pass
    
    def compose(self) -> ComposeResult:
        """Render the music player UI based on current playerctl status."""
        if self.last_metadata is None:
            yield Static("♫ No Media Playing", classes="music-no-media")
            return
        
        current_time = format_time(self.current_position)
        total_time = format_time(self.last_metadata['length'])
        progress_bar = create_progress_bar(self.current_position, self.last_metadata['length'], width=25)
        
        with Vertical(classes="music-main-container"):
            yield Static(self.last_metadata['title'], classes="music-title")
            yield Static(self.last_metadata['artist'], classes="music-artist")
            
            with Horizontal(classes="music-progress-container"):
                yield Static(current_time, classes="music-time", id="current-time")
                yield Static(progress_bar, classes="music-progress-bar", id="progress-bar")
                yield Static(total_time, classes="music-time", id="total-time")
            
            play_icon = "▶" if not self.is_playing else "⏸"
            with Horizontal(classes="music-control-buttons"):
                yield Button("⏮", classes="music-btn-main", id="btn-prev", variant="primary")
                yield Button(play_icon, classes="music-btn-play", id="btn-play", variant="primary")
                yield Button("⏭", classes="music-btn-main", id="btn-next", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks for all music controls."""
        button_id = event.button.id
        
        if button_id == "btn-play":
            self.play_pause()
        elif button_id == "btn-next":
            self.next_track()
        elif button_id == "btn-prev":
            self.previous_track()
    
    def _run_playerctl(self, *args: str):
        """Helper to run playerctl commands safely and trigger a UI refresh."""
        try:
            subprocess.run(
                ['playerctl', *args], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                timeout=1
            )
            self.set_timer(0.1, self.fetch_metadata)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    def play_pause(self):
        """Toggle play/pause state."""
        self._run_playerctl('play-pause')
    
    def next_track(self):
        """Skip to next track."""
        self._run_playerctl('next')
    
    def previous_track(self):
        """Go to previous track."""
        self._run_playerctl('previous')