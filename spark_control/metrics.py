"""Read counters once per 5 seconds, only on demand. No GPU compute context."""
import ctypes as c
import os
import math
import threading
import time
from collections import deque
from pathlib import Path


def read(path):
    try:
        return Path(path).read_text()
    except OSError:
        return ""


class Utilization(c.Structure):
    _fields_ = [("gpu", c.c_uint), ("memory", c.c_uint)]


def filesystem_usage(path='/'):
    volume = os.statvfs(path)
    total = volume.f_blocks * volume.f_frsize
    free = volume.f_bfree * volume.f_frsize
    available = volume.f_bavail * volume.f_frsize
    used = total - free
    return {'disk': round(used/2**40, 3), 'disk_total_tib': round(total/2**40, 3),
            'disk_mount': path, 'disk_total_bytes': total, 'disk_used_bytes': used,
            'disk_available_bytes': available, 'disk_reserved_free_bytes': max(0, free-available),
            'disk_used_percent': used/total*100 if total else None,
            'disk_df_percent': math.ceil(used/(used+available)*100) if used+available else None}


class GPU:
    def __init__(self):
        self.lib = None
        try:
            lib = c.CDLL("libnvidia-ml.so.1")
            if lib.nvmlInit_v2() != 0:
                return
            self.device = c.c_void_p()
            if lib.nvmlDeviceGetHandleByIndex_v2(c.c_uint(0), c.byref(self.device)) == 0:
                self.lib = lib
        except (OSError, AttributeError):
            pass

    def query(self, function, *args, output=c.c_uint):
        if not self.lib:
            return None
        result = output()
        try:
            rc = getattr(self.lib, function)(self.device, *args, c.byref(result))
            if rc == 0:
                return result
        except AttributeError:
            pass
        return None

    def name(self):
        if not self.lib:
            return None
        try:
            value = c.create_string_buffer(96)
            if self.lib.nvmlDeviceGetName(self.device, value, c.c_uint(len(value))) == 0:
                return value.value.decode('utf-8', errors='replace')
        except AttributeError:
            pass
        return None

    def collect(self):
        result = {}
        for name, function, args, output in [
            ("temp", "nvmlDeviceGetTemperature", (c.c_uint(0),), c.c_uint),
            ("power", "nvmlDeviceGetPowerUsage", (), c.c_uint),
            ("gpu_clock_mhz", "nvmlDeviceGetClockInfo", (c.c_uint(1),), c.c_uint),
            ("memory_clock_mhz", "nvmlDeviceGetClockInfo", (c.c_uint(2),), c.c_uint),
            ("clock_event_reasons", "nvmlDeviceGetCurrentClocksThrottleReasons", (), c.c_ulonglong),
        ]:
            value = self.query(function, *args, output=output)
            result[name] = None if value is None else value.value
        if result["power"] is not None:
            result["power"] /= 1000
        utilization = self.query("nvmlDeviceGetUtilizationRates", output=Utilization)
        result["gpu"] = None if utilization is None else utilization.gpu
        return result


class Collector:
    interval = 5

    def __init__(self):
        self.gpu = GPU()
        self.lock = threading.Lock()
        self.history = deque(maxlen=720)
        self.previous = None
        self.latest = None
        self.collected_at = 0
        self.collections = 0

    @staticmethod
    def counters():
        cpus = {}
        for line in read("/proc/stat").splitlines():
            parts = line.split()
            if parts and parts[0].startswith("cpu"):
                values = list(map(int, parts[1:9]))  # guest already included in user/nice
                cpus[parts[0]] = (sum(values), values[3] + values[4])
        interfaces = {}
        for line in read("/proc/net/dev").splitlines()[2:]:
            name, numbers = line.split(":", 1)
            name = name.strip()
            # Physical devices only; avoids bridge/Tailscale/veth double counting.
            if not Path(f"/sys/class/net/{name}/device").exists():
                continue
            fields = numbers.split()
            interfaces[name] = [int(fields[0]), int(fields[8])]
        disks = {}
        for line in read("/proc/diskstats").splitlines():
            fields = line.split()
            name = fields[2]
            if not Path(f"/sys/block/{name}/device").exists():
                continue  # whole physical block devices only, excludes partitions
            disks[name] = [int(fields[5]) * 512, int(fields[9]) * 512]
        return cpus, interfaces, disks

    def snapshot(self):
        with self.lock:
            now = time.monotonic()
            if self.latest is not None and now - self.collected_at < self.interval:
                return self.latest
            cpus, interfaces, disks = self.counters()
            elapsed = now - self.collected_at
            usable = self.previous is not None and elapsed <= self.interval * 3
            previous_cpu, previous_net, previous_disk = self.previous or ({}, {}, {})

            def rates(current, old):
                if not usable or set(current) != set(old) or not current:
                    return [None, None]
                delta = [sum(current[k][i] - old[k][i] for k in current) for i in range(2)]
                return [round(x / elapsed / 1e6, 3) if x >= 0 else None for x in delta]

            loads = {}
            for key, (total, idle) in cpus.items():
                before = previous_cpu.get(key)
                change = total - before[0] if before else 0
                loads[key] = round(100 * (1 - (idle - before[1]) / change), 1) if usable and change > 0 else None
            mem = {parts[0].rstrip(":"): int(parts[1]) * 1024 for line in read("/proc/meminfo").splitlines() if len(parts := line.split()) >= 2}
            total = mem.get("MemTotal", 0)
            available = mem.get("MemAvailable", 0)
            storage = filesystem_usage('/')
            clocks = [int(value) / 1e6 for path in Path("/sys/devices/system/cpu").glob("cpu[0-9]*/cpufreq/scaling_cur_freq") if (value := read(path).strip()).isdigit()]
            sensors = []
            for hwmon in sorted(Path("/sys/class/hwmon").glob("hwmon*")):
                for path in sorted(hwmon.glob("temp*_input")):
                    try:
                        sensors.append({"id": f"{hwmon.name}/{path.stem}", "source": read(hwmon / "name").strip(), "label": read(path.with_name(path.name.replace("_input", "_label"))).strip() or path.stem, "celsius": float(read(path)) / 1000})
                    except ValueError:
                        pass
            self.latest = {
                "timestamp": time.time(), **self.gpu.collect(),
                "cpu": loads.get("cpu"), "cores": {k: v for k, v in loads.items() if k != "cpu"},
                "cpu_clock_ghz": [min(clocks), max(clocks)] if clocks else None,
                "memory": round((total - available) / 2**30, 2), "memory_total_gib": round(total / 2**30, 2),
                "memory_available_gib": round(available / 2**30, 2),
                "swap_used_gib": round((mem.get("SwapTotal", 0) - mem.get("SwapFree", 0)) / 2**30, 2),
                **storage,
                "network": rates(interfaces, previous_net), "diskio": rates(disks, previous_disk),
                "interfaces": list(interfaces), "disks": list(disks), "sensors": sensors[:64],
                "speed": None, "source": "live", "rate_warming_up": not usable,
            }
            self.previous = (cpus, interfaces, disks)
            self.collected_at = now
            self.collections += 1
            self.history.append(self.latest)
            return self.latest

    def samples(self):
        with self.lock:
            cutoff = time.time() - 3600
            return [row for row in self.history if row["timestamp"] >= cutoff]
