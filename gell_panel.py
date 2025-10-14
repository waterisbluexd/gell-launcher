#!/usr/bin/env python3
from textual.widgets import Static

class GellPanel(Static):
    """A panel displaying Gell information."""

    def __init__(self):
        super().__init__()
        self.classes = "panel-content"

    def on_mount(self) -> None:
        """Handle panel mount."""
        self.update_display()

    def update_display(self) -> None:
        """Update the panel display."""
        # You can customize this content based on what you want to display
        self.update("Welcome to Gell")

    def on_panel_focus(self) -> None:
        """Handle when panel gains focus."""
        self.update_display()