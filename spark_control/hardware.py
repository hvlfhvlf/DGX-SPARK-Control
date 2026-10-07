"""Hardware identity without capacity guesses or a background inventory process."""
import json
import os
import platform
import re
from pathlib import Path


def parse_installed_memory(output):
    """Sum only populated SMBIOS type 17 Size fields (dmidecode binary units)."""
    sizes = re.findall(r'^\s*Size:\s*(\d+)\s+(kB|MB|GB|TB)\s*$', output, re.M)
    if not sizes:
        return None
    units = {'kB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
    # Unknown populated devices must not turn a partial sum into a total.
    fields = re.findall(r'^\s*Size:\s*(.*?)\s*$', output, re.M)
    if any(not re.fullmatch(r'\d+\s+(kB|MB|GB|TB)|No Module Installed', field) for field in fields):
        return None
    return sum(int(value) * units[unit] for value, unit in sizes) or None


def identity(directory, gpu_name):
    from .metrics import read
    total = re.search(r'^MemTotal:\s+(\d+)', read('/proc/meminfo'), re.M)
    installed = None
    try:
        saved = json.loads((Path(directory) / 'hardware.json').read_text())
        value = saved.get('installed_memory_bytes')
        if type(value) is int and 0 < value < 2**60:
            installed = value
    except (OSError, ValueError, AttributeError):
        pass
    return {
        'product': read('/sys/devices/virtual/dmi/id/product_name').strip() or None,
        'architecture': platform.machine(), 'logical_cpus': os.cpu_count(),
        'gpu_name': gpu_name,
        'memory_kind': 'unified' if gpu_name and 'GB10' in gpu_name else 'system',
        'installed_memory_bytes': installed,
        'installed_memory_source': 'SMBIOS type 17' if installed else None,
        'os_memory_bytes': int(total[1]) * 1024 if total else None,
        'os_memory_source': '/proc/meminfo:MemTotal',
    }
