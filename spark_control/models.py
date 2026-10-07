"""Explicit service allowlist; no browser-supplied command execution."""
import os
import re
import subprocess
import threading
import time
from pathlib import Path


class Models:
    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.scan_lock = threading.Lock()
        self.last_scan = 0
        self.cached_at = 0
        self.cached = []

    def registry(self):
        return self.config.value.get("models", [])[:32]

    @staticmethod
    def unit(model):
        unit = model.get("service", "")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}\.service", unit):
            raise ValueError("Model requires a valid allowlisted user service")
        return unit

    def listing(self):
        with self.lock:
            if time.monotonic() - self.cached_at < 10:
                return self.cached
            result = []
            for model in self.registry():
                try:
                    unit = self.unit(model)
                    call = subprocess.run(["systemctl", "--user", "is-active", unit], capture_output=True, text=True, timeout=2)
                    status = call.stdout.strip()
                except (ValueError, OSError, subprocess.TimeoutExpired):
                    status = "unavailable"
                result.append({"id": str(model["id"]), "name": str(model.get("name", model["id"])), "engine": str(model.get("engine", "custom")), "state": status, "controllable": bool(model.get("allow_control", False)) and status != "unavailable"})
            self.cached, self.cached_at = result, time.monotonic()
            return result

    def action(self, identifier, action):
        if action not in ("start", "stop"):
            raise ValueError("Unsupported action")
        with self.lock:
            model = next((m for m in self.registry() if m["id"] == identifier), None)
            if not model or model.get("allow_control") is not True:
                raise ValueError("This model is not enabled for control")
            unit = self.unit(model)
            result = subprocess.run(["systemctl", "--user", "--no-block", action, unit], capture_output=True, timeout=5)
            if result.returncode:
                raise ValueError("Service manager rejected the operation; inspect its local journal")
            self.cached_at = 0
            return {"accepted": True, "id": identifier, "action": action, "note": "Accepted by systemd; refresh status to check completion"}

    def discover(self):
        if not self.scan_lock.acquire(blocking=False):
            raise ValueError("A scan is already running")
        try:
            start = time.monotonic()
            if start - self.last_scan < 10:
                raise ValueError("Wait 10 seconds between scans")
            self.last_scan = start
            matches, visited, truncated = [], 0, False
            for root in self.config.value.get("model_roots", [])[:8]:
                root = Path(root).expanduser().resolve()
                if not root.is_dir():
                    continue
                for directory, dirs, files in os.walk(root, followlinks=False):
                    dirs[:] = sorted(d for d in dirs if not d.startswith(".") and not (Path(directory) / d).is_symlink())
                    if len(Path(directory).relative_to(root).parts) >= 5:
                        dirs[:] = []
                    for filename in files:
                        visited += 1
                        if len(matches) >= 128 or visited >= 10000 or time.monotonic() - start > 2:
                            truncated = True
                            break
                        if filename.endswith((".gguf", ".safetensors.index.json")) or filename == "config.json":
                            path = Path(directory) / filename
                            if not path.is_symlink():
                                matches.append({"path": str(path), "status": "needs_review"})
                    if truncated:
                        break
                if truncated:
                    break
            return {"matches": matches, "truncated": truncated, "roots_configured": len(self.config.value.get("model_roots", [])), "note": "Candidates only. No weights loaded, hashed, installed or removed."}
        finally:
            self.scan_lock.release()
