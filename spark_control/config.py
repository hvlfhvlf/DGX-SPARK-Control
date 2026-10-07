import json
import hashlib
import hmac
import os
import secrets
import threading
from pathlib import Path

DEFAULTS = {"schema_version": 1, "spark_name": "DGX_SPARK", "models": [], "model_roots": []}


class Config:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.directory / "config.json"
        self.lock = threading.RLock()
        self.value = {**DEFAULTS, **(json.loads(self.path.read_text()) if self.path.exists() else {})}
        if self.value["schema_version"] != 1:
            raise ValueError("Unsupported config schema; restore a compatible release")
        token_file = self.directory / "access-token"
        if not token_file.exists():
            fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as stream:
                stream.write(secrets.token_urlsafe(32))
        self.token = token_file.read_text().strip()
        if not self.token:
            raise ValueError("Access token cannot be empty")
        password_file = self.directory / 'password.json'
        self.password = json.loads(password_file.read_text()) if password_file.exists() else None
        self.save()

    def set_password(self, password):
        if not isinstance(password, str) or not 4 <= len(password) <= 128:
            raise ValueError('Password must contain 4-128 characters')
        salt = secrets.token_bytes(16)
        iterations = 600000
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
        record = {'algorithm': 'pbkdf2-sha256', 'iterations': iterations, 'salt': salt.hex(), 'hash': digest.hex()}
        temporary = self.directory / 'password.tmp'
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(record, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.directory / 'password.json')
        self.password = record

    def check_password(self, password):
        if not self.password or not isinstance(password, str) or len(password) > 128:
            return False
        record = self.password
        try:
            iterations = int(record['iterations'])
            if record['algorithm'] != 'pbkdf2-sha256' or not 100000 <= iterations <= 2000000:
                return False
            digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(record['salt']), iterations)
            return hmac.compare_digest(digest, bytes.fromhex(record['hash']))
        except (ValueError, KeyError, TypeError):
            return False

    def save(self):
        with self.lock:
            temporary = self.path.with_suffix(".tmp")
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w") as stream:
                json.dump(self.value, stream, ensure_ascii=False, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)

    def rename(self, name):
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 32:
            raise ValueError("Spark name must contain 1–32 characters")
        if any(ord(char) < 32 for char in name):
            raise ValueError("Control characters are not allowed")
        with self.lock:
            self.value["spark_name"] = name.strip()
            self.save()
        return self.value["spark_name"]
