"""
Services Panel - Display and manage system services with interactive controls
"""
import subprocess
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Button
from textual.reactive import reactive


class NetworkControl(Container):
    """Network enable/disable control."""

    is_enabled = reactive(False)

    def __init__(self):
        super().__init__(classes="service-control-item-left")
        self.button = Button(
            "Wifi: Disabled",
            id="btn-network-toggle",
            classes="service-btn-left"
        )
        self.refresh_status()

    def compose(self) -> ComposeResult:
        """Compose the network control layout."""
        yield self.button

    def refresh_status(self) -> None:
        """Check network status using nmcli."""
        try:
            result = subprocess.run(
                ["nmcli", "networking", "connectivity"],
                capture_output=True, text=True, timeout=2
            )
            connectivity = result.stdout.strip()
            self.is_enabled = connectivity in ["full", "limited", "portal"]
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            self.is_enabled = False

    def watch_is_enabled(self, is_enabled: bool) -> None:
        """Update button label when is_enabled changes."""
        self.button.label = f"Wifi: {'Enabled' if is_enabled else 'Disabled'}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle network button press."""
        if event.button.id == "btn-network-toggle":
            self.toggle_network()

    def toggle_network(self) -> None:
        """Toggle network state."""
        if self.is_enabled:
            self.disable_network()
        else:
            self.enable_network()

    def enable_network(self) -> None:
        """Enable network."""
        try:
            subprocess.run(
                ["nmcli", "networking", "on"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
            )
            import time
            time.sleep(0.5)
            self.refresh_status()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass

    def disable_network(self) -> None:
        """Disable network."""
        try:
            subprocess.run(
                ["nmcli", "networking", "off"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
            )
            import time
            time.sleep(0.5)
            self.refresh_status()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass


class BluetoothControl(Container):
    """Bluetooth enable/disable control."""

    is_enabled = reactive(False)

    def __init__(self):
        super().__init__(classes="service-control-item-left")
        self.button = Button(
            "BlueTooth: Disabled",
            id="btn-bluetooth-toggle",
            classes="service-btn-left"
        )
        self.refresh_status()

    def compose(self) -> ComposeResult:
        """Compose the bluetooth control layout."""
        yield self.button

    def refresh_status(self) -> None:
        """Check bluetooth status using bluetoothctl."""
        try:
            result = subprocess.run(
                ["bluetoothctl", "show"], capture_output=True, text=True, timeout=2
            )
            self.is_enabled = "Powered: yes" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            self.is_enabled = False

    def watch_is_enabled(self, is_enabled: bool) -> None:
        """Update button label when is_enabled changes."""
        self.button.label = f"BlueTooth: {'Enabled' if is_enabled else 'Disabled'}"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle bluetooth button press."""
        if event.button.id == "btn-bluetooth-toggle":
            self.toggle_bluetooth()

    def toggle_bluetooth(self) -> None:
        """Toggle bluetooth state."""
        if self.is_enabled:
            self.disable_bluetooth()
        else:
            self.enable_bluetooth()

    def enable_bluetooth(self) -> None:
        """Enable bluetooth."""
        try:
            subprocess.run(
                ["bluetoothctl", "power", "on"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
            )
            import time
            time.sleep(0.5)
            self.refresh_status()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass

    def disable_bluetooth(self) -> None:
        """Disable bluetooth."""
        try:
            subprocess.run(
                ["bluetoothctl", "power", "off"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
            )
            import time
            time.sleep(0.5)
            self.refresh_status()
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass


class ServicesPanel(Container):
    """Panel to display system services status with interactive controls."""
    
    def __init__(self):
        super().__init__()
        self.network_control = NetworkControl()
        self.bluetooth_control = BluetoothControl()
    
    def compose(self) -> ComposeResult:
        """Compose the services panel layout."""
        with Horizontal(id="services-main-container"):
            # Left side - Interactive controls (small buttons, long length)
            with Vertical(id="services-left-panel"):
                yield self.network_control
                yield self.bluetooth_control
            
            # Right side - 4 equally spaced buttons
            with Vertical(id="services-right-panel"):
                yield Button("", id="service-btn-1", classes="service-square-btn")
                yield Button("", id="service-btn-2", classes="service-square-btn")
                yield Button("", id="service-btn-3", classes="service-square-btn")
                yield Button("", id="service-btn-4", classes="service-square-btn")
    
    def on_mount(self) -> None:
        """Load services when panel is mounted."""
        self.network_control.refresh_status()
        self.bluetooth_control.refresh_status()
    
    def on_panel_focus(self) -> None:
        """Called when the panel receives focus - refresh services."""
        self.network_control.refresh_status()
        self.bluetooth_control.refresh_status()