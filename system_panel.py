#!/usr/bin/env python3
"""System information panel for Gell Launcher."""

from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Container


def get_system_info() -> dict:
    """Retrieves system uptime and memory information."""
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_h, rem = divmod(uptime_seconds, 3600)
            uptime_m, _ = divmod(rem, 60)
            uptime = f"{int(uptime_h)}h {int(uptime_m)}m"

        with open('/proc/meminfo', 'r') as f:
            meminfo = {line.split(':')[0]: line.split(':')[1].strip() for line in f}
        
        mem_total_kb = int(meminfo['MemTotal'].split()[0])
        mem_available_kb = int(meminfo['MemAvailable'].split()[0])
        mem_used_mb = (mem_total_kb - mem_available_kb) // 1024
        mem_total_mb = mem_total_kb // 1024
        mem_percent = int((mem_used_mb / mem_total_mb) * 100) if mem_total_mb > 0 else 0
        
        return {
            'uptime': uptime,
            'mem_used': mem_used_mb,
            'mem_total': mem_total_mb,
            'mem_percent': mem_percent
        }
    except (FileNotFoundError, KeyError, ValueError):
        return {'uptime': 'N/A', 'mem_used': 0, 'mem_total': 0, 'mem_percent': 0}


class SystemPanel(Container):
    """A panel displaying system information like uptime and memory usage."""
    
    def compose(self) -> ComposeResult:
        """Compose the system panel widgets."""
        info = get_system_info()
        yield Static("System Status", classes="system-title")
        bar = "█" * (info['mem_percent'] // 10) + "░" * (10 - info['mem_percent'] // 10)
        yield Static(f"Uptime: {info['uptime']:>12}", classes="stat-row")
        yield Static(f"Memory: {info['mem_used']}MB / {info['mem_total']}MB", classes="stat-row")
        yield Static(f"Usage:  {bar} {info['mem_percent']}%", classes="stat-row")
    
    def refresh_info(self) -> None:
        """Update the system information display."""
        info = get_system_info()
        bar = "█" * (info['mem_percent'] // 10) + "░" * (10 - info['mem_percent'] // 10)
        
        # Update the static widgets with new information
        stats = list(self.query(Static))
        if len(stats) >= 4:
            stats[1].update(f"Uptime: {info['uptime']:>12}")
            stats[2].update(f"Memory: {info['mem_used']}MB / {info['mem_total']}MB")
            stats[3].update(f"Usage:  {bar} {info['mem_percent']}%")