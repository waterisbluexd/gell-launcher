#!/usr/bin/env python3
"""
Clipboard history panel - displays clipboard history as a proper Widget
"""
import subprocess
from pathlib import Path
from textual.widgets import Static, Button
from textual.containers import VerticalScroll
from textual.app import ComposeResult

HISTORY_FILE = Path.home() / ".cache/gell/clipboard_history.txt"
MAX_HISTORY_ITEMS = 20
MAX_DISPLAY_LENGTH = 150


class ClipboardPanel(Static):
    """A widget that displays clipboard history."""
    
    def __init__(self):
        super().__init__()
        self.history = []
        self.load_history()
    
    def load_history(self):
        """Load clipboard history from file."""
        if HISTORY_FILE.exists():
            try:
                with HISTORY_FILE.open('r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        lines = content.split('\n---CLIP---\n')
                        self.history = [line.strip() for line in lines if line.strip()][:MAX_HISTORY_ITEMS]
            except Exception as e:
                self.log(f"Error loading clipboard: {e}")
                self.history = []
        else:
            self.history = []
    
    def format_display_text(self, text: str, max_lines: int = 3) -> str:
        """Format text for display - truncate to max lines and add ellipsis."""
        lines = text.split('\n')
        display_lines = lines[:max_lines]
        result = '\n'.join(display_lines)
        
        if len(result) > MAX_DISPLAY_LENGTH:
            result = result[:MAX_DISPLAY_LENGTH] + "..."
        elif len(lines) > max_lines:
            result += "\n..."
        
        return result
    
    def compose(self) -> ComposeResult:
        """Compose the clipboard UI."""
        self.load_history()
        
        if not self.history:
            yield Static(
                "No clipboard history\n\nCopy something first!",
                classes="clipboard-empty"
            )
        else:
            with VerticalScroll(id="clipboard-scroll-area"):
                for idx, text in enumerate(self.history):
                    display_text = self.format_display_text(text)
                    yield Button(
                        display_text,
                        id=f"clip-btn-{idx}",
                        classes="clipboard-btn"
                    )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        button_id = event.button.id
        if button_id and button_id.startswith("clip-btn-"):
            try:
                idx = int(button_id.split("-")[-1])
                if 0 <= idx < len(self.history):
                    self.set_clipboard(self.history[idx])
                    self.notify(f"Copied: {self.history[idx][:50]}...")
            except (ValueError, IndexError):
                pass
    
    def set_clipboard(self, text: str):
        """Set clipboard content using wl-copy."""
        try:
            subprocess.run(
                ['wl-copy'],
                input=text,
                text=True,
                timeout=1,
                check=False
            )
        except Exception:
            pass
    
    def refresh_display(self):
        """Reload and refresh the display."""
        self.load_history()
        self.refresh(recompose=True)