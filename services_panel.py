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
    network_name = reactive("")
    last_click_time = 0

    def __init__(self):
        super().__init__(classes="wifi-control")
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
        """Check network status and connected SSID using nmcli."""
        try:
            # Check connectivity
            result = subprocess.run(
                ["nmcli", "networking", "connectivity"],
                capture_output=True, text=True, timeout=2
            )
            connectivity = result.stdout.strip()
            self.is_enabled = connectivity in ["full", "limited", "portal"]
            
            # Get connected network name if enabled
            if self.is_enabled:
                try:
                    # Try to get active connection name
                    ssid_result = subprocess.run(
                        ["nmcli", "-g", "NAME", "connection", "show", "--active"],
                        capture_output=True, text=True, timeout=2
                    )
                    connections = ssid_result.stdout.strip().split('\n')
                    # Filter out empty lines and non-wifi connections
                    for conn in connections:
                        if conn and not conn.startswith('lo') and conn.strip():
                            self.network_name = conn.strip()
                            break
                    else:
                        self.network_name = ""
                except Exception:
                    self.network_name = ""
            else:
                self.network_name = ""
                
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            self.is_enabled = False
            self.network_name = ""

    def watch_is_enabled(self, is_enabled: bool) -> None:
        """Update button label when is_enabled changes."""
        self.update_button_label()
    
    def watch_network_name(self, network_name: str) -> None:
        """Update button label when network_name changes."""
        self.update_button_label()

    def update_button_label(self) -> None:
        """Update button label based on status."""
        if hasattr(self, 'button'):
            if not self.is_enabled:
                self.button.label = "Wifi: Disabled"
            elif self.network_name:
                self.button.label = f"Wifi: {self.network_name}"
            else:
                self.button.label = "Wifi: Enabled - Connect to network"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle network button press - single click toggle, double click open nmtui."""
        if event.button.id == "btn-network-toggle":
            import time
            current_time = time.time()
            
            # Double click detection (within 0.5 seconds)
            if current_time - self.last_click_time < 0.5:
                self.open_nmtui()
                self.last_click_time = 0  # Reset to prevent triple-click
            else:
                self.toggle_network()
                self.last_click_time = current_time

    def toggle_network(self) -> None:
        """Toggle network state."""
        if self.is_enabled:
            self.disable_network()
        else:
            self.enable_network()

    def enable_network(self) -> None:
        """Enable network and try to auto-connect."""
        try:
            subprocess.run(
                ["nmcli", "networking", "on"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
            )
            import time
            time.sleep(1.5)  # Wait for auto-connect
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

    def open_nmtui(self) -> None:
        """Open nmtui in a new terminal window."""
        try:
            # Try different terminal emulators
            terminals = [
                ["kitty", "-e", "nmtui"],
                ["alacritty", "-e", "nmtui"],
                ["gnome-terminal", "--", "nmtui"],
                ["xterm", "-e", "nmtui"]
            ]
            
            for terminal_cmd in terminals:
                try:
                    subprocess.Popen(terminal_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except FileNotFoundError:
                    continue
        except Exception:
            pass


class BluetoothControl(Container):
    """Bluetooth enable/disable control."""

    is_enabled = reactive(False)
    connected_device = reactive("")
    last_click_time = 0

    def __init__(self):
        super().__init__(classes="bluetooth-control")
        self.button = Button(
            "Bluetooth: Disabled",
            id="btn-bluetooth-toggle",
            classes="service-btn-left"
        )
        self.refresh_status()

    def compose(self) -> ComposeResult:
        """Compose the bluetooth control layout."""
        yield self.button

    def refresh_status(self) -> None:
        """Check bluetooth status and connected devices using bluetoothctl."""
        try:
            # Check if bluetooth is powered on
            result = subprocess.run(
                ["bluetoothctl", "show"], capture_output=True, text=True, timeout=2
            )
            self.is_enabled = "Powered: yes" in result.stdout
            
            # Get connected device name if enabled
            if self.is_enabled:
                try:
                    # Use bluetoothctl info to get connected devices
                    devices_result = subprocess.run(
                        ["bluetoothctl", "devices"],
                        capture_output=True, text=True, timeout=2
                    )
                    
                    # Check each device to see if it's connected
                    for line in devices_result.stdout.strip().split('\n'):
                        if line.startswith('Device'):
                            parts = line.split(maxsplit=2)
                            if len(parts) >= 3:
                                mac = parts[1]
                                name = parts[2]
                                
                                # Check if this device is connected
                                info_result = subprocess.run(
                                    ["bluetoothctl", "info", mac],
                                    capture_output=True, text=True, timeout=2
                                )
                                if "Connected: yes" in info_result.stdout:
                                    self.connected_device = name
                                    break
                    else:
                        self.connected_device = ""
                except Exception:
                    self.connected_device = ""
            else:
                self.connected_device = ""
                
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            self.is_enabled = False
            self.connected_device = ""

    def watch_is_enabled(self, is_enabled: bool) -> None:
        """Update button label when is_enabled changes."""
        self.update_button_label()
    
    def watch_connected_device(self, connected_device: str) -> None:
        """Update button label when connected_device changes."""
        self.update_button_label()

    def update_button_label(self) -> None:
        """Update button label based on status."""
        if hasattr(self, 'button'):
            if not self.is_enabled:
                self.button.label = "Bluetooth: Disabled"
            elif self.connected_device:
                self.button.label = f"Bluetooth: {self.connected_device}"
            else:
                self.button.label = "Bluetooth: Enabled - Connect device"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle bluetooth button press - single click toggle, double click open bluetoothctl."""
        if event.button.id == "btn-bluetooth-toggle":
            import time
            current_time = time.time()
            
            # Double click detection (within 0.5 seconds)
            if current_time - self.last_click_time < 0.5:
                self.open_bluetooth_manager()
                self.last_click_time = 0  # Reset to prevent triple-click
            else:
                self.toggle_bluetooth()
                self.last_click_time = current_time

    def toggle_bluetooth(self) -> None:
        """Toggle bluetooth state."""
        if self.is_enabled:
            self.disable_bluetooth()
        else:
            self.enable_bluetooth()

    def enable_bluetooth(self) -> None:
        """Enable bluetooth and try to auto-connect to known devices."""
        try:
            subprocess.run(
                ["bluetoothctl", "power", "on"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
            )
            
            # Try to connect to paired devices
            import time
            time.sleep(1)
            
            # Get list of paired devices
            paired_result = subprocess.run(
                ["bluetoothctl", "devices", "Paired"],
                capture_output=True, text=True, timeout=2
            )
            
            # Try to connect to first paired device
            devices = paired_result.stdout.strip().split('\n')
            if devices and devices[0]:
                parts = devices[0].split()
                if len(parts) >= 2:
                    mac = parts[1]
                    subprocess.run(
                        ["bluetoothctl", "connect", mac],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                    )
            
            time.sleep(1)
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

    def open_bluetooth_manager(self) -> None:
        """Open bluetooth manager in a new terminal window."""
        try:
            # Try blueman first (GUI), then bluetoothctl (TUI)
            bluetooth_managers = [
                ["blueman-manager"],
                ["kitty", "-e", "bluetoothctl"],
                ["alacritty", "-e", "bluetoothctl"],
                ["gnome-terminal", "--", "bluetoothctl"],
                ["xterm", "-e", "bluetoothctl"]
            ]
            
            for manager_cmd in bluetooth_managers:
                try:
                    subprocess.Popen(manager_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except FileNotFoundError:
                    continue
        except Exception:
            pass


class FanControl(Container):
    """Fan control with rotating icon and mode cycling."""

    # Fan modes: silent -> performance -> turbo -> auto -> silent
    FAN_MODES = ["silent", "performance", "turbo", "auto"]
    FAN_ICONS = {
        "silent": "─",
        "performance": "╱",
        "turbo": "│",
        "auto": "╲"
    }

    current_mode = reactive(0)  # Index into FAN_MODES

    def __init__(self):
        super().__init__(classes="fan-control")
        mode = self.FAN_MODES[self.current_mode]
        icon = self.FAN_ICONS[mode]
        self.button = Button(
            icon,
            id="btn-fan-toggle",
            classes="service-square-btn"
        )

    def compose(self) -> ComposeResult:
        """Compose the fan control layout."""
        yield self.button

    def get_label(self) -> str:
        """Get current button label with icon."""
        mode = self.FAN_MODES[self.current_mode]
        icon = self.FAN_ICONS[mode]
        return f"{icon}"

    def watch_current_mode(self, mode_idx: int) -> None:
        """Update button label when mode changes."""
        if hasattr(self, 'button'):
            self.button.label = self.get_label()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle fan button press."""
        if event.button.id == "btn-fan-toggle":
            self.cycle_fan_mode()

    def cycle_fan_mode(self) -> None:
        """Cycle through fan modes."""
        self.current_mode = (self.current_mode + 1) % len(self.FAN_MODES)
        mode = self.FAN_MODES[self.current_mode]
        
        # Apply fan mode without sudo (adjust commands based on your system)
        try:
            # Example for systems with fan control utilities
            # You may need to adjust these commands for your specific hardware
            if mode == "silent":
                subprocess.run(
                    ["system76-power", "profile", "battery"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
                )
            elif mode == "performance":
                subprocess.run(
                    ["system76-power", "profile", "balanced"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
                )
            elif mode == "turbo":
                subprocess.run(
                    ["system76-power", "profile", "performance"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
                )
            elif mode == "auto":
                # Reset to auto/default
                subprocess.run(
                    ["system76-power", "profile", "balanced"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            # Silently fail if commands don't work
            pass


class ServicesPanel(Container):
    """Panel to display system services status with interactive controls."""
    
    def __init__(self):
        super().__init__()
        self.network_control = NetworkControl()
        self.bluetooth_control = BluetoothControl()
        self.fan_control = FanControl()
    
    def on_mount(self) -> None:
        """Set up periodic refresh when panel is mounted."""
        self.set_interval(3.0, self.refresh_all_controls)
    
    def refresh_all_controls(self) -> None:
        """Refresh all control statuses."""
        self.network_control.refresh_status()
        self.bluetooth_control.refresh_status()
    
    def compose(self) -> ComposeResult:
        """Compose the services panel layout."""
        with Horizontal(id="services-main-container"):
            # Left side - Interactive controls (small buttons, long length)
            with Vertical(id="services-left-panel"):
                with Container(classes="service-control-item-left-top"):
                    yield self.network_control
                    yield self.bluetooth_control
                with Container(classes="service-control-item-left-bottom"):
                    pass  # Empty space for now
            
            # Right side - 4 equally spaced buttons
            with Vertical(id="services-right-panel"):
                yield self.fan_control
                yield Button("☾", id="service-btn-sleep", classes="service-square-btn")
                yield Button("↻", id="service-btn-restart", classes="service-square-btn")
                yield Button("⏻", id="service-btn-shutdown", classes="service-square-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for power controls."""
        if event.button.id == "service-btn-sleep":
            self.sleep_system()
        elif event.button.id == "service-btn-restart":
            self.restart_system()
        elif event.button.id == "service-btn-shutdown":
            self.shutdown_system()

    def sleep_system(self) -> None:
        """Put system to sleep."""
        try:
            subprocess.Popen(
                ["systemctl", "suspend"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

    def restart_system(self) -> None:
        """Restart the system."""
        try:
            subprocess.Popen(
                ["systemctl", "reboot"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

    def shutdown_system(self) -> None:
        """Shutdown the system."""
        try:
            subprocess.Popen(
                ["systemctl", "poweroff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            pass