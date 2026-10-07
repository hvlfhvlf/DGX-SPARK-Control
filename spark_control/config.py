import json
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
        self.save()

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
