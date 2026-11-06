"""Single-process server; bounded threads, payloads, history and authentication state."""
import argparse
import hmac
import hashlib
import json
import math
import secrets
import mimetypes
import os
import subprocess
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs

from .config import Config
from .metrics import Collector
from .models import Models
from .services import Services, ServiceError
from .hardware import identity
from .sessions import Sessions
from .programs import Programs
from .power import Power
from .inference import Inference
from .connections import Connections
from .service_updates import Updates
from .service_autostart import Autostart

ROOT = Path(__file__).resolve().parent.parent
VERSION = (ROOT / "VERSION").read_text().strip()


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 32

    def __init__(self, address, config):
        self.config = config
        self.collector = Collector()
        self.hardware = identity(config.directory, self.collector.gpu.name())
        self.models = Models(config)
        self.services = Services(config)
        self.updates = Updates(self.services.registry)
        self.autostart = Autostart(self.services.registry)
        self.inference = Inference(self.services)
        self.connections = Connections(self.services)
        self.programs = Programs()
        self.power = Power(config)
        self.slots = threading.BoundedSemaphore(8)
        self.history_epoch = secrets.token_hex(8)
        self.events = deque(maxlen=200)
        self.failure_lock = threading.Lock()
        self.failures = deque(maxlen=60)
        self.sessions = Sessions(config)
        super().__init__(address, Handler)

    def process_request(self, request, address):
        # Bounded backpressure: eight workers, one waiting accept, bounded OS backlog.
        # Short bursts wait for a slot; sustained overload gets an explicit retryable
        # response rather than an unexplained connection reset. No extra threads.
        if not self.slots.acquire(timeout=0.25):
            try:
                payload = b'{"error":"Server busy. Retry shortly."}'
                request.settimeout(0.2)
                request.sendall(b'HTTP/1.1 503 Service Unavailable\r\n'
                                b'Content-Type: application/json\r\nRetry-After: 1\r\n'
                                b'Cache-Control: no-store\r\nConnection: close\r\n'
                                + f'Content-Length: {len(payload)}\r\n\r\n'.encode() + payload)
            except OSError:
                pass
            finally:
                request.close()
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            request.settimeout(10)
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    server_version = "DGX-SPARK-Control"

    def log_message(self, *_):
        pass  # Never log tokens, model paths or arbitrary requests.

    def reply(self, status, data, content_type="application/json; charset=utf-8"):
        payload = json.dumps(data, ensure_ascii=False, allow_nan=False).encode() if not isinstance(data, bytes) else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(payload)

    def authenticated(self):
        supplied = self.headers.get("Authorization", "").removeprefix("Bearer ")
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc != self.headers.get("Host"):
            self.reply(403, {"error": "Origin mismatch"})
            return False
        valid_session = self.server.sessions.valid(supplied)
        if not valid_session and not hmac.compare_digest(supplied.encode(), self.server.config.token.encode()):
            now = time.monotonic()
            with self.server.failure_lock:
                while self.server.failures and now - self.server.failures[0] > 60:
                    self.server.failures.popleft()
                limited = len(self.server.failures) >= 30
                self.server.failures.append(now)
            self.reply(429 if limited else 401, {"error": "Sign in required"})
            return False
        return True

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/info":
            self.reply(200, {"version": VERSION, "mode": "live", "auth_required": True, "auth_mode": "password" if self.server.config.password else "token"})
            return
        if path.startswith("/api/"):
            if not self.authenticated():
                return
            if path == "/api/settings":
                self.reply(200, {"spark_name": self.server.config.value["spark_name"], "version": VERSION})
            elif path == "/api/hardware":
                self.reply(200, self.server.hardware)
            elif path == "/api/metrics":
                self.reply(200, self.server.collector.snapshot())
            elif path == "/api/history":
                rows = self.server.collector.samples()
                query = parse_qs(urlsplit(self.path).query)
                if query.get('incremental') != ['1']:
                    self.reply(200, rows)  # Compatibility for older clients.
                else:
                    try:
                        since = float(query.get('since', ['0'])[0])
                        if not math.isfinite(since) or since < 0:
                            raise ValueError()
                    except (ValueError, OverflowError):
                        self.reply(400, {'error': 'Invalid history cursor'})
                        return
                    reset = (query.get('epoch', [''])[0] != self.server.history_epoch or
                             bool(rows and (since < rows[0]['timestamp'] or since > rows[-1]['timestamp'])))
                    self.reply(200, {'epoch': self.server.history_epoch, 'reset': reset,
                                     'samples': rows if reset else [r for r in rows if r['timestamp'] > since]})
            elif path == "/api/models":
                try:
                    listing = self.server.services.listing()
                    self.reply(200, [dict(id=s['id'], name=s['name'], engine=s['adapter'], state='active' if s['state']=='running' else s['state'], controllable=s['controllable']) for s in listing['services']])
                except (ValueError, OSError, subprocess.TimeoutExpired):
                    self.reply(503, {"error": "Services unavailable"})
            elif path == "/api/services/autostart":
                try:
                    sid = parse_qs(urlsplit(self.path).query).get("id", [""])[0]
                    self.reply(200, self.server.autostart.status(sid))
                except (ValueError, OSError, subprocess.SubprocessError):
                    self.reply(409, {"error": "autostart_unavailable"})
            elif path == "/api/services/update":
                try:
                    sid = parse_qs(urlsplit(self.path).query).get('id', [''])[0]
                    self.reply(200, self.server.updates.status(sid))
                except (ValueError, OSError, subprocess.SubprocessError):
                    self.reply(409, {'error': 'update_status_unavailable'})
            elif path == "/api/services":
                try:
                    self.reply(200, self.server.services.listing())
                except (ValueError, OSError, subprocess.TimeoutExpired):
                    self.reply(503, {"error": "Services unavailable"})
            elif path in ('/api/inference', '/api/connections/settings'):
                try:
                    sid=parse_qs(urlsplit(self.path).query).get('id',[None])[0]
                    result=self.server.inference.snapshot(sid) if path.endswith('inference') else self.server.connections.settings(sid)
                    self.reply(200,result)
                except (ValueError, OSError, subprocess.TimeoutExpired):
                    self.reply(503, {'error':'Service data unavailable'})
            elif path == '/api/models/roots':
                self.reply(200, self.server.models.roots())
            elif path == "/api/events":
                self.reply(200, self.server.services.recent_events())
            elif path == "/api/programs":
                self.reply(200, self.server.programs.snapshot())
            elif path == "/api/power/status":
                self.reply(200, self.server.power.status())
            elif path == "/api/health":
                self.reply(200, {"status": "ok", "version": VERSION, "collections": self.server.collector.collections, "inference_collections": self.server.inference.collections, "history_samples": len(self.server.collector.history), "max_history_samples": 720, "max_http_workers": 8})
            else:
                self.reply(404, {"error": "Unknown API"})
            return
        web = (ROOT / "web").resolve()
        file = (web / unquote(path).lstrip("/")).resolve() if path != "/" else web / "index.html"
        if not file.is_relative_to(web) or not file.is_file() or file.suffix not in (".html", ".js", ".css", ".svg", ".ttf", ".woff2", ".md", ".txt"):
            self.reply(404, {"error": "Not found"})
            return
        self.reply(200, file.read_bytes(), mimetypes.guess_type(file.name)[0] or "application/octet-stream")

    def do_POST(self):
        path = urlsplit(self.path).path
        if path != '/api/login' and not self.authenticated():
            return
        origin = self.headers.get('Origin')
        if origin and urlsplit(origin).netloc != self.headers.get('Host'):
            self.reply(403, {'error': 'Origin mismatch'})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                self.reply(413, {"error": "Request size must be 1–4096 bytes"})
                return
            data = json.loads(self.rfile.read(length))
            if path == '/api/login':
                now = time.monotonic()
                with self.server.failure_lock:
                    while self.server.failures and now - self.server.failures[0] > 60:
                        self.server.failures.popleft()
                    limited = len(self.server.failures) >= 30
                if limited:
                    self.reply(429, {'error': 'Too many attempts. Try again in a minute.'})
                elif not self.server.config.check_password(data.get('password')):
                    with self.server.failure_lock:
                        self.server.failures.append(now)
                    self.reply(401, {'error': 'Password not accepted'})
                else:
                    token = self.server.sessions.issue()
                    self.reply(200, {'session': token, 'expires_in': None, 'persistence': 'until_logout_or_password_reset'})
            elif path == '/api/logout':
                self.server.sessions.revoke(self.headers.get('Authorization', '').removeprefix('Bearer '))
                self.reply(200, {'ok': True})
            elif path == "/api/settings":
                self.reply(200, {"spark_name": self.server.config.rename(data.get("spark_name"))})
            elif path in ('/api/power/prepare', '/api/power/confirm'):
                if (self.server.config.directory / 'service-update.lock').exists():
                    raise ServiceError('update_in_progress')
                session = hashlib.sha256(self.headers.get('Authorization', '').encode()).hexdigest()
                try:
                    result = self.server.power.prepare(session, data.get('action')) if path.endswith('/prepare') else self.server.power.confirm(session, data)
                except ValueError as error:
                    raise ServiceError(str(error)) from None
                self.reply(202 if path.endswith('/confirm') else 200, result)
            elif path == "/api/models/action":
                result = self.server.services.action(data.get("id"), data.get("action"))
                self.reply(202, result)
            elif path == "/api/services/autostart":
                self.reply(200, self.server.autostart.set(data))
            elif path == "/api/services/update/check":
                try:
                    self.reply(200, self.server.updates.check(data.get('id')))
                except ServiceError:
                    raise
                except Exception:
                    raise ServiceError('update_check_failed') from None
            elif path == "/api/services/update/apply":
                self.reply(202, self.server.updates.apply(data.get('id'), data.get('ticket')))
            elif path == "/api/services/action":
                self.reply(202, self.server.services.action(data.get('id'), data.get('action'), data.get('profile_id'), data.get('revision')))
            elif path == "/api/services/open":
                self.reply(200, self.server.services.open_app(data))
            elif path == "/api/services/discover":
                self.reply(200, self.server.services.discover())
            elif path == "/api/services/register":
                self.reply(200, self.server.services.register_candidate(data.get('candidate_id'), data.get('revision')))
            elif path == "/api/services/display":
                self.reply(200, self.server.services.update_display(data))
            elif path == "/api/services/order":
                self.reply(200, self.server.services.reorder(data))
            elif path == "/api/events/clear":
                self.reply(200, self.server.services.clear_events(data.get('through')))
            elif path == "/api/models/discover":
                self.reply(200, self.server.models.discover())
            elif path == '/api/models/roots':
                self.reply(200, self.server.models.set_roots(data.get('roots')))
            elif path == '/api/models/register':
                self.reply(200, self.server.models.register(data.get('candidate_id'), data.get('name')))
            elif path == '/api/connections/discover':
                self.reply(200, self.server.connections.discover())
            elif path == '/api/connections/check':
                self.reply(200, self.server.connections.check(data))
            elif path == '/api/connections/save':
                self.reply(200, self.server.connections.save(data.get('ticket')))
            else:
                self.reply(404, {"error": "Unknown API"})
        except ServiceError as error:
            self.reply(409, {"error": str(error)})
        except (ValueError, TypeError, AttributeError):
            self.reply(400, {"error": "Invalid request or operation unavailable"})
        except (OSError, subprocess.TimeoutExpired):
            self.reply(503, {"error": "Could not persist settings or access service"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--data-dir", default=os.path.expanduser("~/.local/share/dgx-spark-control"))
    args = parser.parse_args()
    config = Config(args.data_dir)
    server = Server((args.bind, args.port), config)
    print(f"DGX-SPARK-Control {VERSION}: {args.bind}:{args.port}; data: {args.data_dir}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
