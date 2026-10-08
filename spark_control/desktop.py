"""One-shot desktop helpers. Never poll, change Serve routing, or expose tokens."""
import json
import re
import subprocess
import uuid

LOCAL_URL = 'http://127.0.0.1:8767'
RELEASES = 'https://github.com/hvlfhvlf/DGX-SPARK-Control/releases'


def dashboard_url(config):
    for host, site in config.get('Web', {}).items():
        if not re.fullmatch(r'[a-zA-Z0-9.-]+\.ts\.net:[0-9]+', host):
            continue
        proxy = site.get('Handlers', {}).get('/', {}).get('Proxy')
        if proxy in (LOCAL_URL, LOCAL_URL + '/', 'http://localhost:8767'):
            if config.get('AllowFunnel', {}).get(host):
                continue
            name, port = host.rsplit(':', 1)
            return 'https://' + name + ('' if port == '443' else ':' + port)
    return None


def connection():
    try:
        result = subprocess.run(['tailscale', 'serve', 'status', '--json'], capture_output=True, text=True, timeout=5, check=True)
        url = dashboard_url(json.loads(result.stdout))
        return {'url': url, 'state': 'connected' if url else 'needs_setup'}
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
        return {'url': None, 'state': 'unavailable'}


def launch(command):
    # Keep browsers/setup outside the monitoring slice; run only explicit argv.
    subprocess.Popen(['systemd-run', '--user', '--collect', '--unit=dgx-desktop-'+uuid.uuid4().hex[:10], *command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def open_url(url):
    launch(['/usr/bin/xdg-open', url])
