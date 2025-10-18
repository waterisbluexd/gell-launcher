"""
Services Panel - Display and manage system services with interactive controls
"""
import subprocess
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Button
from textual.reactive import reactive
from textual.events import MouseDown, MouseMove, MouseUp
from textual.message import Message
from textual.containers import Container, Horizontal, Vertical
from rich.text import Text


class Slider(Widget):
    """A draggable slider widget."""
    
    DEFAULT_CSS = """
    Slider {
        height: 1;
        width: 100%;
    }
    """
    
    class Changed(Message):
        """Posted when the slider value changes."""
        def __init__(self, slider: "Slider", value: float) -> None:
            self.slider = slider
            self.value = value
            super().__init__()
    
    value = reactive(0.0)  # 0.0 to 1.0
    is_dragging = reactive(False)
    
    def __init__(
        self,
        initial_value: float = 0.5,
        fill_char: str = "━",
        empty_char: str = "─",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.value = max(0.0, min(1.0, initial_value))
        self.fill_char = fill_char
        self.empty_char = empty_char
    
    def render(self) -> Text:
        """Render the slider bar."""
        width = self.size.width
        if width < 1:
            return Text("")
        
        # Calculate filled portion
        filled_width = int(self.value * width)
        
        # Build the slider visual
        filled = self.fill_char * filled_width
        empty = self.empty_char * (width - filled_width)
        
        return Text(filled + empty)
    
    def on_mouse_down(self, event: MouseDown) -> None:
        """Handle mouse down - start dragging."""
        self.is_dragging = True
        self._update_value_from_mouse(event.x)
        self.capture_mouse()
    
    def on_mouse_move(self, event: MouseMove) -> None:
        """Handle mouse move - update value while dragging."""
        if self.is_dragging:
            self._update_value_from_mouse(event.x)
    
    def on_mouse_up(self, event: MouseUp) -> None:
        """Handle mouse up - stop dragging."""
        if self.is_dragging:
            self.is_dragging = False
            self.release_mouse()
    
    def _update_value_from_mouse(self, x: int) -> None:
        """Update slider value based on mouse position."""
        width = self.size.width
        if width > 0:
            new_value = max(0.0, min(1.0, x / width))
            if abs(new_value - self.value) > 0.01:  # Threshold to reduce updates
                self.value = new_value
                self.post_message(self.Changed(self, self.value))
    
    def watch_value(self, value: float) -> None:
        """Refresh display when value changes."""
        self.refresh()


class BrightnessControl(Container):
    """Brightness slider control with icon and percentage."""
    
    brightness = reactive(50)  # 0-100
    
    def __init__(self):
        super().__init__(classes="slider-control")
        self.slider = Slider(initial_value=0.5)
        self._get_current_brightness()
    
    def compose(self):
        with Container(classes="slider-container"):
            yield Static("☀", classes="slider-icon")
            yield self.slider
            self.value_label = Static(f"{self.brightness}%", classes="slider-value")
            yield self.value_label
    
    def on_mount(self) -> None:
        """Update slider value on mount."""
        self.slider.value = self.brightness / 100.0
        self.slider.add_class("slider-bar")
    
    def on_slider_changed(self, event: Slider.Changed) -> None:
        """Handle slider value changes."""
        if event.slider == self.slider:
            self.brightness = int(event.value * 100)
            self._set_brightness(self.brightness)
            self.value_label.update(f"{self.brightness}%")
    
    def _get_current_brightness(self) -> None:
        """Get current brightness using brightnessctl."""
        try:
            result = subprocess.run(
                ["brightnessctl", "get"],
                capture_output=True, text=True, timeout=1
            )
            current = int(result.stdout.strip())
            
            # Get max brightness
            result_max = subprocess.run(
                ["brightnessctl", "max"],
                capture_output=True, text=True, timeout=1
            )
            max_bright = int(result_max.stdout.strip())
            
            self.brightness = int((current / max_bright) * 100)
        except Exception:
            self.brightness = 50
    
    def _set_brightness(self, percent: int) -> None:
        """Set brightness using brightnessctl."""
        try:
            subprocess.run(
                ["brightnessctl", "set", f"{percent}%"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
        except Exception:
            pass


class VolumeControl(Container):
    """Volume slider control with icon and percentage."""
    
    volume = reactive(50)  # 0-100
    
    def __init__(self):
        super().__init__(classes="slider-control")
        self.slider = Slider(initial_value=0.5)
        self._get_current_volume()
    
    def compose(self):
        with Container(classes="slider-container"):
            yield Static("♪", classes="slider-icon")
            yield self.slider
            self.value_label = Static(f"{self.volume}%", classes="slider-value")
            yield self.value_label
    
    def on_mount(self) -> None:
        """Update slider value on mount."""
        self.slider.value = self.volume / 100.0
        self.slider.add_class("slider-bar")
    
    def on_slider_changed(self, event: Slider.Changed) -> None:
        """Handle slider value changes."""
        if event.slider == self.slider:
            self.volume = int(event.value * 100)
            self._set_volume(self.volume)
            self.value_label.update(f"{self.volume}%")
    
    def _get_current_volume(self) -> None:
        """Get current volume using pactl."""
        try:
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True, text=True, timeout=1
            )
            # Parse output like: "Volume: front-left: 65536 /  100% / 0.00 dB"
            for part in result.stdout.split():
                if part.endswith('%'):
                    self.volume = int(part.rstrip('%'))
                    break
        except Exception:
            self.volume = 50
    
    def _set_volume(self, percent: int) -> None:
        """Set volume using pactl."""
        try:
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percent}%"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1
            )
        except Exception:
            pass


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
            # Check if networking is enabled
            result = subprocess.run(
                ["nmcli", "networking"],
                capture_output=True, text=True, timeout=2
            )
            networking_status = result.stdout.strip()
            self.is_enabled = networking_status == "enabled"
            
            # Get connected network name if enabled
            if self.is_enabled:
                try:
                    # Get the active Wi-Fi connection
                    ssid_result = subprocess.run(
                        ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
                        capture_output=True, text=True, timeout=2
                    )
                    
                    active_ssid = ""
                    for line in ssid_result.stdout.strip().split('\n'):
                        if line.startswith("yes:"):
                            # The SSID is the part after "yes:"
                            active_ssid = line[4:].strip()
                            break  # Found the active connection
                    
                    self.network_name = active_ssid

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
                subprocess.run(
                    ["system76-power", "profile", "balanced"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3
                )
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass


class ServicesPanel(Container):
    """Panel to display system services status with interactive controls."""
    
    def __init__(self):
        super().__init__()
        self.network_control = NetworkControl()
        self.bluetooth_control = BluetoothControl()
        self.fan_control = FanControl()
        self.brightness_control = BrightnessControl()
        self.volume_control = VolumeControl()
    
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
            with Vertical(id="services-left-panel"):
                with Container(classes="service-control-item-left-top"):
                    yield self.network_control
                    yield self.bluetooth_control
                with Container(classes="service-control-item-left-bottom"):
                    yield self.brightness_control
                    yield self.volume_control
            
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