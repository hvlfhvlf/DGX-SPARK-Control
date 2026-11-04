"""Explicit service allowlist; no browser-supplied command execution."""
import os
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path


class Models:
    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.scan_lock = threading.Lock()
        self.last_scan = 0
        self.cached_at = 0
        self.cached = []
        self.candidates = {}

    def registry(self):
        return self.config.value.get("models", [])[:32]

    def roots(self):
        return dict(roots=self.config.value.get('model_roots', [])[:8], inventory=[dict(id=m['id'],name=m['name'],format=m['format'],exists=Path(m['path']).is_file()) for m in self.config.value.get('model_inventory',[])[:128]])

    def register(self, candidate_id, name):
        with self.scan_lock:
            entry=self.candidates.get(candidate_id) if isinstance(candidate_id,str) else None
            if not entry or time.monotonic()-self.last_scan>300 or not Path(entry['path']).is_file():
                raise ValueError('Search again')
            if not isinstance(name,str) or not 1<=len(name.strip())<=120 or any(ord(c)<32 for c in name):
                raise ValueError('Invalid model name')
            with self.config.lock:
                inventory=self.config.value.get('model_inventory',[])
                if len(inventory)>=128:
                    raise ValueError('Inventory full')
                if not any(m['path']==entry['path'] for m in inventory):
                    inventory.append(dict(id=uuid.uuid4().hex,name=name.strip(),path=entry['path'],format=entry['format']))
                    self.config.value['model_inventory']=inventory
                    self.config.save()
            return self.roots()

    def set_roots(self, roots):
        if not isinstance(roots,list) or len(roots)>8 or any(not isinstance(p,str) or len(p)>512 for p in roots):
            raise ValueError('Invalid roots')
        selected=[]
        for raw in roots:
            path=Path(raw).expanduser().resolve()
            # Only explicitly selected user model directories; never recurse through OS pseudo files.
            if not path.is_dir() or path==Path('/') or any(path==Path(p) or path.is_relative_to(p) for p in ('/proc','/sys','/dev','/etc','/run','/boot')):
                raise ValueError('Invalid model directory')
            if str(path) not in selected:
                selected.append(str(path))
        with self.config.lock:
            self.config.value['model_roots']=selected
            self.config.save()
        return self.roots()

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
            self.candidates={}
            matches, visited, truncated = [], 0, False
            for root in self.config.value.get("model_roots", [])[:8]:
                root = Path(root).expanduser().resolve()
                if not root.is_dir():
                    continue
                for directory, dirs, files in os.walk(root, followlinks=False):
                    visited += 1
                    if visited >= 10000 or time.monotonic() - start > 2:
                        truncated = True
                        break
                    dirs[:] = sorted(d for d in dirs if not d.startswith(".") and not (Path(directory) / d).is_symlink())
                    if len(Path(directory).relative_to(root).parts) >= 5:
                        dirs[:] = []
                    for filename in files:
                        visited += 1
                        if len(matches) >= 128 or visited >= 10000 or time.monotonic() - start > 2:
                            truncated = True
                            break
                        if filename.endswith((".gguf", ".safetensors.index.json", ".safetensors")) or filename == "config.json":
                            path = Path(directory) / filename
                            if not path.is_symlink() or path.resolve().is_relative_to(root):
                                # Index represents sharded weights; do not list every shard as a model.
                                if filename.endswith('.safetensors') and (any(f.endswith('.safetensors.index.json') for f in files) or re.search(r'-\d{5}-of-\d{5}',filename)):
                                    continue
                                matches.append({"path": str(path), "name": path.parent.name if filename in ('config.json','model.safetensors.index.json') else path.stem,
                                                "format": 'GGUF' if filename.endswith('.gguf') else 'safetensors' if 'safetensors' in filename else 'config', "status": "needs_review"})
                    if truncated:
                        break
                if truncated:
                    break
            registered={m['path'] for m in self.config.value.get('model_inventory',[])}
            for entry in matches:
                entry['id']=uuid.uuid4().hex
                entry['registered']=entry['path'] in registered
                self.candidates[entry['id']]=entry.copy()
            return {"matches": matches, "truncated": truncated, "roots_configured": len(self.config.value.get("model_roots", [])), "note": "Candidates only. No weights loaded, hashed, installed or removed."}
        finally:
            self.scan_lock.release()
