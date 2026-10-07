"""Single-process server; bounded threads, payloads, history and authentication state."""
import argparse
import hmac
import json
import mimetypes
import os
import subprocess
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote

from .config import Config
from .metrics import Collector
from .models import Models
from .hardware import identity
from .sessions import Sessions

ROOT = Path(__file__).resolve().parent.parent
VERSION = (ROOT / "VERSION").read_text().strip()


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 16

    def __init__(self, address, config):
        self.config = config
        self.collector = Collector()
        self.hardware = identity(config.directory, self.collector.gpu.name())
        self.models = Models(config)
        self.slots = threading.BoundedSemaphore(8)
        self.events = deque(maxlen=200)
        self.failure_lock = threading.Lock()
        self.failures = deque(maxlen=60)
        self.sessions = Sessions(config)
        super().__init__(address, Handler)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
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
                self.reply(200, self.server.collector.samples())
            elif path == "/api/models":
                self.reply(200, self.server.models.listing())
            elif path == "/api/events":
                self.reply(200, list(self.server.events))
            elif path == "/api/health":
                self.reply(200, {"status": "ok", "version": VERSION, "collections": self.server.collector.collections, "history_samples": len(self.server.collector.history), "max_history_samples": 720, "max_http_workers": 8})
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
            elif path == "/api/models/action":
                result = self.server.models.action(data.get("id"), data.get("action"))
                self.server.events.appendleft({"timestamp": time.time(), "message": f"Service {result['action']} accepted: {result['id']}"})
                self.reply(202, result)
            elif path == "/api/models/discover":
                self.reply(200, self.server.models.discover())
            else:
                self.reply(404, {"error": "Unknown API"})
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
