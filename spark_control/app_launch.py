"""On-demand authenticated handoff to a locally installed Harness. No token storage."""
import http.client
import re
from pathlib import Path
from urllib.parse import urlsplit, parse_qs


def supported(profile):
    return (profile.get('manager', {}).get('unit') == 'deepseek-harness.service'
            and profile.get('allow_control') is True and bool(profile.get('open_url')))


def harness_url(profile):
    # Fixed local source, never a browser-supplied file or command. Read a bounded tail.
    try:
        if not supported(profile):
            raise ValueError()
        base = urlsplit(profile['open_url'])
        if base.scheme != 'https' or base.path not in ('', '/') or base.query or base.fragment or base.username or base.password:
            raise ValueError()
        log = Path.home() / '.local/share/deepseek-harness/logs/web.log'
        with log.open('rb') as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell() - 65536))
            tail = stream.read(65536).decode('utf-8', errors='replace')
        matches = re.findall(r'https?://[^\s\x1b<>"\x27]+\?token=[^\s\x1b<>"\x27]+', tail)
        if not matches:
            raise ValueError()
        launch = urlsplit(matches[-1])
        query = parse_qs(launch.query, strict_parsing=True)
        if (launch.scheme != base.scheme or launch.netloc != base.netloc or launch.path not in ('', '/')
                or launch.fragment or set(query) != {'token'} or len(query['token']) != 1
                or not re.fullmatch(r'[A-Za-z0-9_-]{16,512}', query['token'][0])):
            raise ValueError()
        # Verify against the fixed loopback app without following any redirect.
        conn = http.client.HTTPConnection('127.0.0.1', 3080, timeout=2)
        try:
            conn.request('GET', '/?' + launch.query)
            response = conn.getresponse()
            if (response.status not in (302, 303) or not response.getheader('Set-Cookie')
                    or response.getheader('Location') not in ('/', './')):
                raise ValueError()
        finally:
            conn.close()
        return {'url': base.scheme + '://' + base.netloc + '/?' + launch.query}
    except (OSError, ValueError, http.client.HTTPException):
        # Do not expose logs, cookie headers, tokens or paths in errors.
        raise ValueError('app_launch_unavailable') from None
