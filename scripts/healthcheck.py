import json
import time
import urllib.request
from pathlib import Path

for attempt in range(20):
    try:
        token = (Path.home() / '.local/share/dgx-spark-control/access-token').read_text().strip()
        request = urllib.request.Request('http://127.0.0.1:8767/api/health', headers={'Authorization': 'Bearer ' + token})
        with urllib.request.urlopen(request, timeout=2) as response:
            assert json.load(response)['status'] == 'ok'
        print('Authenticated healthcheck passed')
        break
    except Exception:
        time.sleep(.5)
else:
    raise SystemExit(1)
