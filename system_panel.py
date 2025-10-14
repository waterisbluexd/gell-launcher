#!/usr/bin/env python3
"""System information panel for Gell Launcher."""

import os
from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal, Container

class SystemPanel(Container):
    """A panel displaying system information like uptime and memory usage."""
    DEFAULT_CLASSES = "panel-system"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_timer = None
        self.prev_cpu_stats = {}

    def compose(self) -> ComposeResult:
        """Compose the system panel widgets."""
        with Horizontal(classes="system-bars-container"):
            with Container(classes="system-bar-container"):
                yield Static("CPU", classes="system-title")
                yield Static(id="system-usage-bar-cpu")
            with Container(classes="system-bar-container"):
                yield Static("Memory", classes="system-title")
                yield Static(id="system-usage-bar-mem")
            with Container(classes="system-bar-container"):
                yield Static("Disk", classes="system-title")
                yield Static(id="system-usage-bar-disk")
            with Container(classes="system-bar-container"):
                yield Static("Wifi", classes="system-title")
                yield Static(id="system-usage-bar-wifi")
            with Container(classes="system-bar-container"):
                yield Static("GPU", classes="system-title")
                yield Static(id="system-usage-bar-gpu")

    def on_mount(self) -> None:
        """Start the timer to refresh system info when the widget is mounted."""
        self.refresh_info()
        self.update_timer = self.set_interval(2.0, self.refresh_info)

    def on_unmount(self) -> None:
        """Stop the timer when the widget is unmounted."""
        if self.update_timer:
            self.update_timer.stop()

    def _create_bar_str(self, percent: int) -> str:
        bar_height = 6
        filled_count = round(percent * bar_height / 100)
        empty_count = bar_height - filled_count
        bar_lines = ["░░"] * empty_count + ["██"] * filled_count
        return "\n".join(bar_lines)

    def refresh_info(self) -> None:
        """Update the system information display."""
        info = self.get_system_info()
        
        self.query_one("#system-usage-bar-cpu").update(self._create_bar_str(info.get('cpu_percent', 0)))
        self.query_one("#system-usage-bar-mem").update(self._create_bar_str(info.get('mem_percent', 0)))
        self.query_one("#system-usage-bar-disk").update(self._create_bar_str(info.get('disk_percent', 0)))
        self.query_one("#system-usage-bar-wifi").update(self._create_bar_str(info.get('wifi_percent', 0)))
        self.query_one("#system-usage-bar-gpu").update(self._create_bar_str(info.get('gpu_percent', 0)))

    def get_system_info(self) -> dict:
        """Retrieves system information."""
        info = {}

        # Memory
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = {line.split(':')[0]: line.split(':')[1].strip() for line in f}
            mem_total_kb = int(meminfo['MemTotal'].split()[0])
            mem_available_kb = int(meminfo['MemAvailable'].split()[0])
            mem_used_mb = (mem_total_kb - mem_available_kb) // 1024
            mem_total_mb = mem_total_kb // 1024
            info['mem_percent'] = int((mem_used_mb / mem_total_mb) * 100) if mem_total_mb > 0 else 0
        except (FileNotFoundError, KeyError, ValueError):
            info['mem_percent'] = 0

        # CPU
        try:
            with open('/proc/stat', 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                if line.startswith('cpu '):
                    cpu_stats = [int(x) for x in line.split()[1:]]
                    if self.prev_cpu_stats:
                        prev_idle = self.prev_cpu_stats['idle'] + self.prev_cpu_stats['iowait']
                        idle = cpu_stats[3] + cpu_stats[4]

                        prev_non_idle = (self.prev_cpu_stats['user'] + self.prev_cpu_stats['nice'] +
                                         self.prev_cpu_stats['system'] + self.prev_cpu_stats['irq'] +
                                         self.prev_cpu_stats['softirq'] + self.prev_cpu_stats['steal'])
                        non_idle = (cpu_stats[0] + cpu_stats[1] + cpu_stats[2] +
                                    cpu_stats[5] + cpu_stats[6] + cpu_stats[7])

                        prev_total = prev_idle + prev_non_idle
                        total = idle + non_idle

                        totald = total - prev_total
                        idled = idle - prev_idle
                        
                        cpu_percent = (totald - idled) * 100 / totald if totald > 0 else 0
                        info['cpu_percent'] = int(cpu_percent)

                    self.prev_cpu_stats = {
                        'user': cpu_stats[0], 'nice': cpu_stats[1], 'system': cpu_stats[2],
                        'idle': cpu_stats[3], 'iowait': cpu_stats[4], 'irq': cpu_stats[5],
                        'softirq': cpu_stats[6], 'steal': cpu_stats[7]
                    }
                    break
        except (FileNotFoundError, IndexError, ValueError, ZeroDivisionError):
            info['cpu_percent'] = 0

        # Disk
        try:
            st = os.statvfs('/')
            free = st.f_bavail * st.f_frsize
            total = st.f_blocks * st.f_frsize
            used = total - free
            info['disk_percent'] = int(used * 100 / total) if total > 0 else 0
        except (FileNotFoundError, OSError):
            info['disk_percent'] = 0

        # Wifi
        try:
            with open('/proc/net/wireless', 'r') as f:
                lines = f.readlines()
            if len(lines) > 2:
                parts = lines[2].split()
                link_quality = parts[2].strip('.')
                max_quality = 70 # default max quality for /proc/net/wireless is 70
                wifi_percent = (int(link_quality) / max_quality) * 100
                info['wifi_percent'] = int(wifi_percent)
            else:
                info['wifi_percent'] = 0
        except (FileNotFoundError, IndexError, ValueError):
            info['wifi_percent'] = 0
            
        # GPU - Placeholder
        info['gpu_percent'] = 0 # Getting GPU usage is complex and hardware-specific

        return info