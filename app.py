from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Static
from textual.screen import Screen
from theme import load_wal_colors, generate_css

class GellLauncher(Screen[None]):
    def compose(self) -> ComposeResult:
        with Vertical(id="gell-container"):
            with Container(id="Gell"):
                yield Static("", classes="panel-content")
            
            with Container(id="Apps"):
                yield Static("", classes="panel-content")
            
            with Container(id="Input"):
                yield Input(
                    placeholder="Type to search apps...",
                    id="search-input"
                )
    
    def on_mount(self) -> None:
        """Set border titles after mounting"""
        self.query_one("#Gell").border_title = "Gell"
        self.query_one("#Apps").border_title = "Apps"
        self.query_one("#Input").border_title = "Input"
        # Focus the search input
        self.query_one("#search-input").focus()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes"""
        search_term = event.value
        # For now, just show what's being typed
        if search_term:
            self.query_one("#Gell Static").update(f"Searching for: {search_term}")
        else:
            self.query_one("#Gell Static").update("")

class GellApp(App[None]):
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("escape", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        colors = load_wal_colors()
        self.CSS = generate_css(colors)
        self._disable_tooltips = True
    
    def on_mount(self) -> None:
        self.push_screen(GellLauncher())
    
    def action_quit(self) -> None:
        self.exit()

if __name__ == "__main__":
    app = GellApp()
    import sys
    if "--inline" not in sys.argv:
        sys.argv.append("--inline")
    app.run()