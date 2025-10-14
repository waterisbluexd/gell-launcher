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
        self.prev_cpu_stats = None
        self.prev_net_stats = None
        self.prev_disk_stats = None

    def compose(self) -> ComposeResult:
        """Compose the system panel widgets."""
        with Horizontal(classes="system-bars-container"):
            with Container(classes="system-bar-container"):
                yield Static("0%", id="system-percent-cpu", classes="system-percent")
                yield Static(id="system-usage-bar-cpu")
                yield Static("CPU", classes="system-title")
            with Container(classes="system-bar-container"):
                yield Static("0%", id="system-percent-mem", classes="system-percent")
                yield Static(id="system-usage-bar-mem")
                yield Static("MEM", classes="system-title")
            with Container(classes="system-bar-container"):
                yield Static("0%", id="system-percent-wifi", classes="system-percent")
                yield Static(id="system-usage-bar-wifi")
                yield Static("NET", classes="system-title")
            with Container(classes="system-bar-container"):
                yield Static("0%", id="system-percent-disk", classes="system-percent")
                yield Static(id="system-usage-bar-disk")
                yield Static("DISK", classes="system-title")
            with Container(classes="system-bar-container"):
                yield Static("0%", id="system-percent-gpu0", classes="system-percent")
                yield Static(id="system-usage-bar-gpu0")
                yield Static("GPU0", classes="system-title")
            with Container(classes="system-bar-container"):
                yield Static("0%", id="system-percent-gpu1", classes="system-percent")
                yield Static(id="system-usage-bar-gpu1")
                yield Static("GPU1", classes="system-title")

    def on_mount(self) -> None:
        """Start the timer to refresh system info when the widget is mounted."""
        # Initialize baseline stats
        self._read_cpu_stats()
        self._read_net_stats()
        self._read_disk_stats()
        
        self.refresh_info()
        self.update_timer = self.set_interval(2.0, self.refresh_info)

    def on_unmount(self) -> None:
        """Stop the timer when the widget is unmounted."""
        if self.update_timer:
            self.update_timer.stop()

    def _create_bar_str(self, percent: int) -> str:
        bar_height = 6  # Increased height for better visibility
        filled_count = round(percent * bar_height / 100)
        empty_count = bar_height - filled_count
        
        # Right-align the bars with padding
        bar_lines = ["░░    "] * empty_count + ["██    "] * filled_count
        return "\n".join(bar_lines)

    def _read_cpu_stats(self):
        """Read CPU statistics from /proc/stat."""
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
                if line.startswith('cpu '):
                    cpu_stats = [int(x) for x in line.split()[1:]]
                    return {
                        'user': cpu_stats[0], 'nice': cpu_stats[1], 'system': cpu_stats[2],
                        'idle': cpu_stats[3], 'iowait': cpu_stats[4], 'irq': cpu_stats[5],
                        'softirq': cpu_stats[6], 'steal': cpu_stats[7] if len(cpu_stats) > 7 else 0
                    }
        except (FileNotFoundError, IndexError, ValueError):
            pass
        return None

    def _read_net_stats(self):
        """Read network statistics from /proc/net/dev."""
        try:
            with open('/proc/net/dev', 'r') as f:
                lines = f.readlines()
            
            total_rx = 0
            total_tx = 0
            
            for line in lines[2:]:  # Skip header lines
                if ':' in line:
                    parts = line.split(':')
                    interface = parts[0].strip()
                    
                    # Skip loopback interface
                    if interface == 'lo':
                        continue
                    
                    stats = parts[1].split()
                    total_rx += int(stats[0])  # Received bytes
                    total_tx += int(stats[8])  # Transmitted bytes
            
            return {'rx': total_rx, 'tx': total_tx}
        except (FileNotFoundError, IndexError, ValueError):
            pass
        return None

    def _read_disk_stats(self):
        """Read disk I/O statistics from /proc/diskstats."""
        try:
            with open('/proc/diskstats', 'r') as f:
                lines = f.readlines()
            
            total_read = 0
            total_write = 0
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 14:
                    device = parts[2]
                    # Focus on main disks (sda, nvme0n1, etc.), skip partitions
                    if (device.startswith(('sd', 'nvme', 'vd', 'hd')) and 
                        not any(c.isdigit() for c in device[-1])):
                        total_read += int(parts[5])   # sectors read
                        total_write += int(parts[9])  # sectors written
            
            return {'read': total_read, 'write': total_write}
        except (FileNotFoundError, IndexError, ValueError):
            pass
        return None

    def _get_gpu_usage(self):
        """Get GPU usage - supports NVIDIA and AMD."""
        gpu_usages = [0, 0]
        
        # Try NVIDIA
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                capture_output=True, text=True, timeout=1
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines[:2]):  # Max 2 GPUs
                    try:
                        gpu_usages[i] = int(line.strip())
                    except ValueError:
                        pass
                return gpu_usages
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try AMD (radeontop or rocm-smi)
        try:
            import subprocess
            result = subprocess.run(
                ['rocm-smi', '--showuse'],
                capture_output=True, text=True, timeout=1
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for i, line in enumerate(lines):
                    if 'GPU use' in line:
                        try:
                            usage = int(line.split('%')[0].split()[-1])
                            if i < 2:
                                gpu_usages[i] = usage
                        except (ValueError, IndexError):
                            pass
                return gpu_usages
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return gpu_usages

    def refresh_info(self) -> None:
        """Update the system information display."""
        info = self.get_system_info()
        
        # Update both bars and percentage displays
        metrics = ['cpu', 'mem', 'wifi', 'disk', 'gpu0', 'gpu1']
        for metric in metrics:
            value = info.get(f'{metric}_percent', 0)
            self.query_one(f"#system-usage-bar-{metric}").update(self._create_bar_str(value))
            # Add consistent right padding to percentage display
            self.query_one(f"#system-percent-{metric}").update(f"{value}%    ")

    def get_system_info(self) -> dict:
        """Retrieves system information."""
        info = {}

        # Memory
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = {line.split(':')[0]: line.split(':')[1].strip() for line in f}
            mem_total_kb = int(meminfo['MemTotal'].split()[0])
            mem_available_kb = int(meminfo['MemAvailable'].split()[0])
            mem_used_kb = mem_total_kb - mem_available_kb
            info['mem_percent'] = int((mem_used_kb / mem_total_kb) * 100) if mem_total_kb > 0 else 0
        except (FileNotFoundError, KeyError, ValueError):
            info['mem_percent'] = 0

        # CPU
        current_cpu_stats = self._read_cpu_stats()
        if current_cpu_stats and self.prev_cpu_stats:
            try:
                prev_idle = self.prev_cpu_stats['idle'] + self.prev_cpu_stats['iowait']
                idle = current_cpu_stats['idle'] + current_cpu_stats['iowait']

                prev_non_idle = (self.prev_cpu_stats['user'] + self.prev_cpu_stats['nice'] +
                                 self.prev_cpu_stats['system'] + self.prev_cpu_stats['irq'] +
                                 self.prev_cpu_stats['softirq'] + self.prev_cpu_stats['steal'])
                non_idle = (current_cpu_stats['user'] + current_cpu_stats['nice'] + 
                            current_cpu_stats['system'] + current_cpu_stats['irq'] +
                            current_cpu_stats['softirq'] + current_cpu_stats['steal'])

                prev_total = prev_idle + prev_non_idle
                total = idle + non_idle

                totald = total - prev_total
                idled = idle - prev_idle
                
                if totald > 0:
                    cpu_percent = ((totald - idled) * 100) / totald
                    info['cpu_percent'] = min(100, max(0, int(cpu_percent)))
                else:
                    info['cpu_percent'] = 0
            except (KeyError, ZeroDivisionError):
                info['cpu_percent'] = 0
        else:
            info['cpu_percent'] = 0
        
        self.prev_cpu_stats = current_cpu_stats

        # Network (bandwidth usage)
        current_net_stats = self._read_net_stats()
        if current_net_stats and self.prev_net_stats:
            try:
                rx_diff = current_net_stats['rx'] - self.prev_net_stats['rx']
                tx_diff = current_net_stats['tx'] - self.prev_net_stats['tx']
                
                # Calculate bytes per second (2 second interval)
                total_bytes_per_sec = (rx_diff + tx_diff) / 2.0
                
                # Estimate as percentage of 1 Gbps = 125 MB/s
                # Adjust this based on your connection speed
                max_bytes_per_sec = 125 * 1024 * 1024  # 1 Gbps in bytes
                net_percent = (total_bytes_per_sec / max_bytes_per_sec) * 100
                info['wifi_percent'] = min(100, max(0, int(net_percent)))
            except (KeyError, ZeroDivisionError):
                info['wifi_percent'] = 0
        else:
            info['wifi_percent'] = 0
        
        self.prev_net_stats = current_net_stats

        # Disk I/O
        current_disk_stats = self._read_disk_stats()
        if current_disk_stats and self.prev_disk_stats:
            try:
                read_diff = current_disk_stats['read'] - self.prev_disk_stats['read']
                write_diff = current_disk_stats['write'] - self.prev_disk_stats['write']
                
                # Convert sectors to bytes (512 bytes per sector)
                total_bytes = (read_diff + write_diff) * 512
                
                # Bytes per second over 2 second interval
                bytes_per_sec = total_bytes / 2.0
                
                # Estimate as percentage of typical SSD: ~500 MB/s
                # Adjust based on your disk speed
                max_bytes_per_sec = 500 * 1024 * 1024
                disk_percent = (bytes_per_sec / max_bytes_per_sec) * 100
                info['disk_percent'] = min(100, max(0, int(disk_percent)))
            except (KeyError, ZeroDivisionError):
                info['disk_percent'] = 0
        else:
            info['disk_percent'] = 0
        
        self.prev_disk_stats = current_disk_stats

        # GPU
        gpu_usages = self._get_gpu_usage()
        info['gpu0_percent'] = gpu_usages[0]
        info['gpu1_percent'] = gpu_usages[1]

        return info