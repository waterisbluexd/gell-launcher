import subprocess
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widget import Widget
from textual.widgets import Static

def get_playerctl_metadata():
    """
    Fetch current media info from playerctl.
    Returns a dictionary with track info or None if nothing is playing.
    """
    try:
        # Check if any player is active to avoid unnecessary calls
        result = subprocess.run(
            ['playerctl', '-l'], capture_output=True, text=True, timeout=1
        )
        if not result.stdout.strip():
            return None

        # Fetch all required metadata in a single, more efficient call
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

        # Unpack the metadata
        (title, artist, album, status, position_str, length_micro, art_url, player) = \
            result.stdout.strip().split('\n', 7)
        
        metadata = {
            'title': title or "Unknown Track",
            'artist': artist or "Unknown Artist",
            'album': album or "",
            'status': status or "Stopped",
            'player': player or "Unknown"
        }

        # Safely convert position and length
        try:
            metadata['position'] = int(float(position_str))
        except (ValueError, TypeError):
            metadata['position'] = 0
            
        try:
            metadata['length'] = int(length_micro) // 1000000  # Microseconds to seconds
        except (ValueError, TypeError):
            metadata['length'] = 0

        # Convert file:// URL to a local path
        if art_url.startswith('file://'):
            metadata['art_path'] = art_url[7:]
        else:
            metadata['art_path'] = None
            
        return metadata
        
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        # Handle cases where playerctl isn't installed, times out, or returns unexpected data
        return None


def format_time(seconds: int) -> str:
    """Convert seconds to a standard MM:SS format."""
    if seconds < 0:
        return "0:00"
    mins, secs = divmod(seconds, 60)
    return f"{mins}:{secs:02d}"


def create_progress_bar(position: int, length: int, width: int = 30) -> str:
    """
    Create a text-based progress bar string.
    Example: [━━━━━●────────]
    """
    if length <= 0:
        return "[" + "─" * width + "]"
    
    progress = min(position / length, 1.0)
    filled = int(progress * (width -1))
    
    bar = "━" * filled + "●" + "─" * (width - filled - 1)
    return f"[{bar}]"


class MusicPanel(Widget):
    """A self-contained, self-updating widget for music player controls."""

    def on_mount(self) -> None:
        """Start a timer to automatically refresh the display every second."""
        self.update_timer = self.set_interval(1.0, self.recompose)

    def compose(self) -> ComposeResult:
        """Render the music player UI based on current playerctl status."""
        metadata = get_playerctl_metadata()
        
        if metadata is None:
            yield Static("♫ No Media Playing", classes="music-no-media")
            yield Static("\nPlay something in your browser or music app!", classes="music-hint")
            return
        
        # Extract and format metadata for display
        status_icon = "▶ Playing" if metadata['status'] == "Playing" else "⏸ Paused"
        current_time = format_time(metadata['position'])
        total_time = format_time(metadata['length'])
        progress_bar = create_progress_bar(metadata['position'], metadata['length'])

        yield Static(f"♫ Now Playing - {status_icon}", classes="music-header")

        with Horizontal(classes="music-content"):
            with Container(classes="music-album-art"):
                yield Static("🎵\n\nAlbum\nArt", classes="album-art-placeholder")
            with Vertical(classes="music-info"):
                yield Static(metadata['title'], classes="music-title")
                yield Static(metadata['artist'], classes="music-artist")
                if metadata['album']:
                    yield Static(metadata['album'], classes="music-album")
                yield Static(f"via {metadata['player'].title()}", classes="music-player")

        with Horizontal(classes="music-progress-container"):
            yield Static(current_time, classes="music-time")
            yield Static(progress_bar, classes="music-progress-bar")
            yield Static(total_time, classes="music-time")

        with Horizontal(classes="music-controls"):
            yield Static("Controls: ", classes="control-label")
            yield Static("[Space] Play/Pause", classes="control-hint")
            yield Static("[N] Next", classes="control-hint")
            yield Static("[P] Prev", classes="control-hint")
            yield Static("[,] Vol-", classes="control-hint")
            yield Static("[.] Vol+", classes="control-hint")

    def _run_playerctl(self, *args: str):
        """Helper to run playerctl commands safely and trigger a UI refresh."""
        try:
            subprocess.run(
                ['playerctl', *args], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                timeout=1
            )
            # Recompose after a short delay to allow the player state to update
            self.call_later(self.recompose)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Ignore errors if playerctl is not found or times out
            pass

    def play_pause(self):
        self._run_playerctl('play-pause')

    def next_track(self):
        self._run_playerctl('next')

    def previous_track(self):
        self._run_playerctl('previous')

    def volume_up(self):
        self._run_playerctl('volume', '0.05+')

    def volume_down(self):
        self._run_playerctl('volume', '0.05-')
