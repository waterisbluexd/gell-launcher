#!/usr/bin/env python3
"""Clock panel for Gell Launcher."""

from datetime import datetime
from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Container

class GellPanel(Container):
    """A panel displaying a digital clock with date."""
    DEFAULT_CLASSES = "panel-clock"

    # Large block-style digits (7 lines high, 5 chars wide)
    DIGITS = {
        '0': [
            "██████",
            "██  ██",
            "██  ██",
            "██  ██",
            "██  ██",
            "██  ██",
            "██████"
        ],
        '1': [
            "  ██  ",
            "████  ",
            "  ██  ",
            "  ██  ",
            "  ██  ",
            "  ██  ",
            "██████"
        ],
        '2': [
            "█████",
            "   ██",
            "   ██",
            "█████",
            "██   ",
            "██   ",
            "█████"
        ],
        '3': [
            "█████",
            "   ██",
            "   ██",
            "█████",
            "   ██",
            "   ██",
            "█████"
        ],
        '4': [
            "██  ██",
            "██  ██",
            "██  ██",
            "██████",
            "    ██",
            "    ██",
            "    ██"
        ],
        '5': [
            "█████",
            "██   ",
            "██   ",
            "█████",
            "   ██",
            "   ██",
            "█████"
        ],
        '6': [
            "██████",
            "██    ",
            "██    ",
            "██████",
            "██  ██",
            "██  ██",
            "██████"
        ],
        '7': [
            "██████",
            "    ██",
            "   ██",
            "  ██ ",
            " ██  ",
            "██   ",
            "██   "
        ],
        '8': [
            "██████",
            "██  ██",
            "██  ██",
            "██████",
            "██  ██",
            "██  ██",
            "██████"
        ],
        '9': [
            "██████",
            "██  ██",
            "██  ██",
            "██████",
            "    ██",
            "    ██",
            "██████"
        ],
        ':': [
            "     ",
            "  ██ ",
            "  ██ ",
            "     ",
            "  ██ ",
            "  ██ ",
            "     "
        ],
        ' ': [
            "     ",
            "     ",
            "     ",
            "     ",
            "     ",
            "     ",
            "     "
        ]
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_timer = None
        self._app_ref = None

    def compose(self) -> ComposeResult:
        """Compose the clock panel widgets."""
        yield Static("", id="clock-time", classes="clock-time")
        yield Static("", id="clock-date", classes="clock-date")

    def start_clock_early(self, app_instance) -> None:
        """Start clock updates before widget is mounted (for prewarming).
        
        This allows the clock to start ticking immediately at boot time,
        so it's ready when the user opens the launcher.
        """
        if not self.update_timer:
            self._app_ref = app_instance
            try:
                # Start the timer on the app instance instead of the widget
                self.update_timer = app_instance.set_interval(1.0, self.update_display)
            except Exception as e:
                # Fallback: will start normally on mount
                pass

    def on_mount(self) -> None:
        """Start the timer to refresh clock when the widget is mounted."""
        self.update_display()
        # Only start timer if not already started by start_clock_early()
        if not self.update_timer:
            self.update_timer = self.set_interval(1.0, self.update_display)

    def on_unmount(self) -> None:
        """Stop the timer when the widget is unmounted."""
        if self.update_timer:
            self.update_timer.stop()
            self.update_timer = None

    def render_large_text(self, text: str) -> str:
        """Convert text to large block-style digits."""
        lines = [""] * 7
        
        for char in text:
            if char in self.DIGITS:
                digit = self.DIGITS[char]
                for i in range(7):
                    lines[i] += digit[i] + " "
        
        return "\n".join(lines)

    def update_display(self) -> None:
        """Update the clock display with current time and date."""
        now = datetime.now()
        
        # Format time as HH:MM
        time_str = now.strftime("%H:%M")
        large_time = self.render_large_text(time_str)
        
        # Format date as "Friday, March 15"
        date_str = now.strftime("%A, %B %d")
        
        # Update the widgets
        try:
            self.query_one("#clock-time").update(large_time)
            self.query_one("#clock-date").update(date_str)
        except Exception:
            pass  # Widget might not be mounted yet

    def on_panel_focus(self) -> None:
        """Handle when panel gains focus."""
        self.update_display()