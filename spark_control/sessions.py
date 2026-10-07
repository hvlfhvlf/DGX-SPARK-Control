"""Bounded persisted session hashes: restarts retain login, password reset revokes it."""
import hashlib
import json
import os
import secrets
import threading
import time


class Sessions:

    def __init__(self, config):
        self.path = config.directory / 'sessions.json'
        self.lock = threading.Lock()
        self.generation = hashlib.sha256(json.dumps(config.password or {}, sort_keys=True).encode()).hexdigest()
        self.values = {}
        try:
            if self.path.stat().st_size <= 16384:
                saved = json.loads(self.path.read_text())
                if saved.get('generation') == self.generation:
                    self.values = {key: stamp for key, stamp in list(saved['sessions'].items())[:32]
                                   if len(key) == 64 and isinstance(stamp, (int, float))
                                   and (saved.get('schema_version') == 2 or stamp > time.time())}
        except (OSError, ValueError, KeyError, AttributeError, TypeError):
            pass

    @staticmethod
    def key(token):
        return hashlib.sha256(token.encode()).hexdigest()

    def save(self):
        temporary = self.path.with_suffix('.tmp')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump({'schema_version': 2, 'generation': self.generation, 'sessions': self.values}, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path)

    def valid(self, token):
        if not token or len(token) > 256:
            return False
        with self.lock:
            return self.key(token) in self.values

    def issue(self):
        token = secrets.token_urlsafe(32)
        now = time.time()
        with self.lock:
            if len(self.values) >= 32:
                self.values.pop(next(iter(self.values)))
            self.values[self.key(token)] = now
            self.save()
        return token

    def revoke(self, token):
        with self.lock:
            self.values.pop(self.key(token), None)
            self.save()
