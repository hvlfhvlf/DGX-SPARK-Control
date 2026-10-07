"""Read-only runtime check; no inference requests, model mutations or token output."""
import concurrent.futures
import json
import subprocess
import time
import urllib.request
from pathlib import Path

token = (Path.home() / '.local/share/dgx-spark-control/access-token').read_text().strip()


def request(path):
    req = urllib.request.Request('http://127.0.0.1:8767/api/' + path, headers={'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def resource():
    rows = subprocess.check_output(['systemctl', '--user', 'show', 'dgx-spark-control', '-p', 'MemoryCurrent', '-p', 'MemoryPeak', '-p', 'MemoryMax', '-p', 'CPUUsageNSec', '-p', 'ControlGroup'], text=True)
    result = dict(line.split('=', 1) for line in rows.splitlines())
    for key in list(result):
        if result[key].isdigit():
            result[key] = int(result[key])
    cgroup = Path('/sys/fs/cgroup') / result.pop('ControlGroup').lstrip('/')
    result['memory_events'] = (cgroup / 'memory.events').read_text().strip()
    return result


before = request('health')
idle_start = resource()
time.sleep(15)
after = request('health')
idle_end = resource()
start = time.monotonic()
load_start = resource()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for tick in range(7):
        list(pool.map(lambda _: request('metrics'), range(4)))
        time.sleep(5)
duration = time.monotonic() - start
load_end = resource()
cpu_ns = load_end.get('CPUUsageNSec', 0) - load_start.get('CPUUsageNSec', 0)
result = {'version': before['version'], 'idle_seconds': 15, 'idle_collections_delta': after['collections'] - before['collections'], 'idle_resources': idle_end, 'four_clients_seconds': round(duration, 2), 'four_clients_core_cpu_percent': round(cpu_ns / 1e9 / duration * 100, 3), 'loaded_resources': load_end, 'health': request('health'), 'notes': 'Read-only synthetic HTTP clients; no inference benchmark. Memory values are cgroup bytes.'}
assert result['idle_collections_delta'] == 0
assert load_end['MemoryCurrent'] < 512_000_000
assert load_end['MemoryMax'] < 512_000_000
print(json.dumps(result, indent=2))
