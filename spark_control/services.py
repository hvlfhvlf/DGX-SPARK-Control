"""Local service registry and bounded systemd-user operations. No shell or weight loader."""
import argparse
import copy
import fcntl
import http.client
import json
import math
import os
import re
import socket
import subprocess
import threading
import time
import uuid
from .startup import Observations
from .local_http import connection
from .app_launch import supported as app_launch_supported, harness_url
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
UNIT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}\.service\Z")
ADAPTERS = ('process', 'comfyui', 'openai-compatible', 'hermes')
PROPERTIES = 'Id,UnitFileState,LoadState,ActiveState,SubState,MainPID,MemoryCurrent,InvocationID,Result,ExecMainStartTimestampMonotonic,FragmentPath'


class ServiceError(ValueError):
    """Only fixed, non-sensitive codes may cross the API boundary."""


def text(value, maximum=80):
    if not isinstance(value, str) or not 1 <= len(value) <= maximum or any(ord(c) < 32 for c in value):
        raise ServiceError('invalid_text')
    return value


def identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ServiceError('invalid_id')
    return value


def origin(value):
    if value is None:
        return None
    parsed = urlsplit(value)
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
        raise ServiceError('probe_must_be_loopback_origin')
    if not 1024 <= parsed.port <= 65535:
        raise ServiceError('invalid_probe_port')
    return f'http://127.0.0.1:{parsed.port}'


def validate(value):
    if not isinstance(value, dict) or value.get('registry_schema') != 1:
        raise ServiceError('invalid_schema')
    revision = value.get('revision', 0)
    if type(revision) is not int or revision < 0:
        raise ServiceError('invalid_revision')
    result = dict(registry_schema=1, revision=revision, services=[], profiles=[], assets=[])
    for key, limit in [('services', 32), ('profiles', 64), ('assets', 128)]:
        if not isinstance(value.get(key, []), list) or len(value.get(key, [])) > limit:
            raise ServiceError('registry_limit')
    seen = set()
    for s in value.get('services', []):
        sid = identifier(s.get('id'))
        if sid in seen or s.get('adapter') not in ADAPTERS:
            raise ServiceError('invalid_service')
        seen.add(sid)
        result['services'].append(dict(id=sid, name=text(s.get('name')), adapter=s['adapter'],
            default_profile_id=identifier(s.get('default_profile_id'))))
    assets = set()
    for a in value.get('assets', []):
        aid = identifier(a.get('id'))
        if aid in assets:
            raise ServiceError('duplicate_asset')
        assets.add(aid)
        result['assets'].append(dict(id=aid, name=text(a.get('name'))))
    profiles, units = {}, {}
    for p in value.get('profiles', []):
        pid, sid = identifier(p.get('id')), identifier(p.get('service_id'))
        manager = p.get('manager', {})
        unit = manager.get('unit', '')
        if pid in profiles or sid not in seen or manager.get('type') != 'systemd-user' or not UNIT.fullmatch(unit) or unit.startswith('dgx-spark-control'):
            raise ServiceError('invalid_profile')
        if unit in units and units[unit] != sid:
            raise ServiceError('unit_owned_by_another_service')
        units[unit] = sid
        probe = p.get('probe')
        probe = origin(probe.get('origin')) if isinstance(probe, dict) else None
        seconds = p.get('startup_timeout_seconds', 180)
        if type(seconds) is not int or not 5 <= seconds <= 600 or type(p.get('allow_control', False)) is not bool:
            raise ServiceError('invalid_profile_limits')
        groups = p.get('exclusive_groups', [])
        deps = p.get('uses_service_ids', [])
        refs = p.get('asset_ids', [])
        if any(not isinstance(v, list) or len(v) > 16 for v in [groups, deps, refs]):
            raise ServiceError('invalid_references')
        if any(d not in seen or d == sid for d in deps) or any(a not in assets for a in refs):
            raise ServiceError('invalid_references')
        groups = [text(g, 64) for g in groups]
        if probe:
            groups = sorted(set(groups + ['port:' + str(urlsplit(probe).port)]))
        open_url = p.get('open_url')
        if open_url:
            u = urlsplit(open_url)
            if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password or u.query or u.fragment:
                raise ServiceError('invalid_open_url')
            text(open_url, 300)
        normalized = dict(id=pid, service_id=sid, name=text(p.get('name')), manager=dict(type='systemd-user', unit=unit),
            allow_control=p.get('allow_control', False), probe=dict(origin=probe) if probe else None,
            startup_timeout_seconds=seconds, exclusive_groups=groups, uses_service_ids=deps, asset_ids=refs, open_url=open_url)
        for key in ('model_name', 'quantization', 'inference_engine', 'serving_engine'):
            normalized[key] = text(p[key], 120) if p.get(key) is not None else None
        observer=p.get('startup_observer')
        if observer not in (None, 'tensorfold'): raise ServiceError('invalid_startup_observer')
        normalized['startup_observer']=observer
        profiles[pid] = normalized
        result['profiles'].append(normalized)
    for s in result['services']:
        if s['default_profile_id'] not in profiles or profiles[s['default_profile_id']]['service_id'] != s['id']:
            raise ServiceError('invalid_default_profile')
    return result


def atomic(path, value):
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as out:
            json.dump(value, out, ensure_ascii=False, allow_nan=False, indent=2)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


class Registry:
    def __init__(self, directory, legacy=None):
        self.directory = Path(directory)
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.path = self.directory / 'services.json'
        if self.path.exists():
            return
        with self.exclusive():
            if not self.path.exists():
                value = dict(registry_schema=1, revision=0, services=[], profiles=[], assets=[])
                for old in (legacy or [])[:32]:
                    sid = identifier(old['id'])
                    value['services'].append(dict(id=sid, name=old.get('name', sid), adapter='process', default_profile_id=sid))
                    value['profiles'].append(dict(id=sid, service_id=sid, name=old.get('name', sid), manager=dict(type='systemd-user', unit=old['service']), allow_control=old.get('allow_control') is True))
                atomic(self.path, validate(value))

    @contextmanager
    def exclusive(self, check_update=True):
        fd = os.open(self.directory / 'services.lock', os.O_RDWR | os.O_CREAT, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ServiceError('operation_in_progress') from None
            if check_update and (self.directory / 'service-update.lock').exists():
                raise ServiceError('update_in_progress')
            yield
        finally:
            os.close(fd)

    def read(self):
        if self.path.stat().st_size > 256 * 1024:
            raise ServiceError('registry_limit')
        return validate(json.loads(self.path.read_text()))

    def save_locked(self, value, revision):
        value = validate(value)
        current = self.read()
        if current['revision'] != revision:
            raise ServiceError('revision_conflict')
        old_profiles = {p['id']: p for p in current['profiles']}
        new_profiles = {p['id']: p for p in value['profiles']}
        changed = []
        for s in current['services']:
            old = old_profiles[s['default_profile_id']]
            new_s = next((n for n in value['services'] if n['id'] == s['id']), None)
            new = new_profiles.get(new_s['default_profile_id']) if new_s else None
            if not new or old['id'] != new['id'] or old['manager'] != new['manager']:
                changed.append(old['manager']['unit'])
        if changed:
            states = system_states(changed)
            if any(states.get(unit, {}).get("UnitFileState") in ("enabled", "enabled-runtime") for unit in changed):
                raise ServiceError("disable_autostart_before_rebinding")
            if any(process_state(states.get(unit, {})) not in ('stopped', 'failed') for unit in changed):
                raise ServiceError('stop_before_rebinding')
        value['revision'] = revision + 1
        atomic(self.path, value)
        return value

    def apply(self, value, revision):
        with self.exclusive():
            return self.save_locked(value, revision)


def system_states(units):
    if not units:
        return {}
    call = subprocess.run(['systemctl', '--user', 'show', '--property=' + PROPERTIES, '--', *sorted(set(units))], capture_output=True, text=True, timeout=3)
    result = {}
    for block in call.stdout.strip().split('\n\n'):
        fields = dict(line.split('=', 1) for line in block.splitlines() if '=' in line)
        if fields.get('Id'):
            result[fields['Id']] = fields
    return result


def process_state(fields):
    if fields.get('LoadState') != 'loaded':
        return 'unknown'
    return {'active': 'running', 'inactive': 'stopped', 'activating': 'starting', 'deactivating': 'stopping', 'failed': 'failed'}.get(fields.get('ActiveState'), 'unknown')


def local_json(base, path):
    port = urlsplit(origin(base)).port
    conn = connection(port, timeout=1)
    try:
        deadline = time.monotonic() + 2
        conn.request('GET', path, headers={'Accept': 'application/json'})
        response = conn.getresponse()
        if response.status != 200:  # No redirects, credentials, cookies or proxy environment.
            raise ServiceError('endpoint_unavailable')
        chunks, size = [], 0
        while True:
            chunk = response.read1(16384)
            if not chunk:
                break
            size += len(chunk)
            if size > 262144 or time.monotonic() > deadline:
                raise ServiceError('probe_limit')
            chunks.append(chunk)
        value = json.loads(b''.join(chunks))
        if not isinstance(value, dict):
            raise ServiceError('invalid_probe')
        return value
    finally:
        conn.close()


def probe(adapter, profile, state):
    result = dict(readiness='unknown', running_jobs=None, pending_jobs=None, model_count=None)
    if state != 'running':
        return result
    if not profile['probe'] or adapter in ('process', 'hermes'):
        result['readiness'] = 'unsupported'
        return result
    try:
        base = profile['probe']['origin']
        if adapter == 'comfyui':
            info = local_json(base, '/system_stats')
            if not isinstance(info.get('system'), dict) or not isinstance(info.get('devices'), list):
                raise ServiceError('unexpected_endpoint')
            result['readiness'] = 'ready'
            try:
                queue = local_json(base, '/queue')
                for field, key in [('running_jobs', 'queue_running'), ('pending_jobs', 'queue_pending')]:
                    if isinstance(queue.get(key), list):
                        result[field] = len(queue[key])
            except (ValueError, OSError, http.client.HTTPException):
                pass  # Never return workflow contents, prompts or filenames.
        elif adapter == 'openai-compatible':
            info = local_json(base, '/v1/models')
            if not isinstance(info.get('data'), list):
                raise ServiceError('unexpected_endpoint')
            result.update(readiness='ready' if info['data'] else 'loading', model_count=len(info['data']))
    except (ValueError, OSError, http.client.HTTPException):
        result['readiness'] = 'unreachable'
    return result


class Services:
    def __init__(self, config):
        self.registry = Registry(config.directory, config.value.get('models', []))
        self.cache_lock = threading.Lock()
        self.op_lock = threading.Lock()
        self.cached_at, self.cached, self.cached_revision = 0, None, -1
        self.readiness_runs = {}
        self.observations = Observations()
        self.operation_path = self.registry.directory / 'service-operations.json'
        self.operations = []
        self.activity_hidden_path = self.registry.directory / 'activity-hidden.json'
        self.activity_hidden = set()
        try:
            if self.activity_hidden_path.stat().st_size <= 16384:
                hidden = json.loads(self.activity_hidden_path.read_text())
                if isinstance(hidden, list): self.activity_hidden = {v for v in hidden[-200:] if isinstance(v, str)}
        except (OSError, ValueError): pass
        if self.operation_path.exists() and self.operation_path.stat().st_size <= 131072:
            try:
                self.operations = json.loads(self.operation_path.read_text())[-200:]
                for op in self.operations:
                    if op['status'] in ('queued', 'running'):
                        op.update(status='interrupted', code='server_restarted_check_service', finished_at=time.time())
                atomic(self.operation_path, self.operations)
            except (ValueError, KeyError, TypeError):
                self.operations = []
        self.candidates, self.last_scan = {}, 0
        self.probe_cursor = 0

    def listing(self):
        value = self.registry.read()
        with self.cache_lock:
            if self.cached is None or value['revision'] != self.cached_revision or time.monotonic() - self.cached_at >= 5:
                states = system_states([p['manager']['unit'] for p in value['profiles']])
                eligible = [s['id'] for s in value['services']]
                selected = set((eligible + eligible)[self.probe_cursor:self.probe_cursor + 2])
                self.probe_cursor = (self.probe_cursor + 2) % max(1, len(eligible))
                rows, readiness_runs = [], {}
                for service in value['services']:
                    profiles = [p for p in value['profiles'] if p['service_id'] == service['id']]
                    p = next(p for p in profiles if p['id'] == service['default_profile_id'])
                    state = process_state(states.get(p['manager']['unit'], {}))
                    fields=states.get(p['manager']['unit'], {})
                    run=(fields.get('InvocationID'), fields.get('MainPID'), fields.get('ExecMainStartTimestampMonotonic'))
                    readiness_runs[service['id']]=run
                    startup=self.observations.read(p,fields,service['id'] in selected) if p.get('startup_observer') or state=='failed' else None
                    if startup: startup.pop('invocation',None)
                    readiness=probe(service['adapter'],p,state if service['id'] in selected or service['adapter'] in ('process','hermes') else 'unknown')
                    previous=next((r for r in self.cached or [] if r['id']==service['id'] and r['profile_id']==p['id'] and r['state']==state),None)
                    same_run=any(run) and self.readiness_runs.get(service['id'])==run
                    if service['id'] not in selected and previous and same_run and value['revision']==self.cached_revision and time.monotonic()-previous.get('readiness_checked_at',0)<30:
                        readiness={k:previous[k] for k in ('readiness','running_jobs','pending_jobs','model_count')}
                    checked=time.monotonic() if service['id'] in selected else (previous or {}).get('readiness_checked_at',0)
                    rows.append(dict(startup=startup,id=service['id'], name=service['name'], adapter=service['adapter'], state=state,
                        profile_id=p['id'], profile_name=p['name'], controllable=p['allow_control'] and state != 'unknown',
                        model_name=p['model_name'], quantization=p['quantization'], inference_engine=p['inference_engine'], serving_engine=p['serving_engine'],
                        open_url=p['open_url'], authenticated_launch=app_launch_supported(p), profiles=[dict(id=q['id'], name=q['name'], controllable=q['allow_control'], state=process_state(states.get(q['manager']['unit'], {}))) for q in profiles],
                        readiness_checked_at=checked,**readiness))
                self.cached = rows
                self.readiness_runs = readiness_runs
                self.cached_revision, self.cached_at = value['revision'], time.monotonic()
            rows = copy.deepcopy(self.cached)
        with self.op_lock:
            ops = copy.deepcopy(self.operations[-20:])
        for row in rows:
            row['operation'] = next((o for o in reversed(ops) if o['service_id'] == row['id']), None)
        return dict(revision=value['revision'], services=rows, operations=ops,
                    maintenance=(self.registry.directory / 'service-update.lock').exists())

    def open_app(self, data):
        with self.registry.exclusive():
            value = self.registry.read()
            if type(data.get('revision')) is not int or data['revision'] != value['revision']:
                raise ServiceError('revision_conflict')
            service = next((s for s in value['services'] if s['id'] == data.get('id')), None)
            if not service:
                raise ServiceError('app_launch_unavailable')
            profile = next(p for p in value['profiles'] if p['id'] == service['default_profile_id'])
            if not app_launch_supported(profile):
                raise ServiceError('app_launch_unavailable')
            unit = profile['manager']['unit']
            if process_state(system_states([unit]).get(unit, {})) != 'running':
                raise ServiceError('app_launch_unavailable')
            try:
                return harness_url(profile)
            except ValueError:
                raise ServiceError('app_launch_unavailable') from None

    def update_operation(self, op, **changes):
        with self.op_lock:
            op.update(changes)
            atomic(self.operation_path, self.operations)

    def update_display(self, payload):
        """Only public-facing labels, never launch settings or permissions."""
        if not isinstance(payload, dict) or set(payload) != {'id', 'profile_id', 'revision', 'fields'}:
            raise ServiceError('invalid_display_fields')
        fields = payload['fields']
        allowed = {'name', 'model_name', 'quantization', 'inference_engine', 'serving_engine'}
        if not isinstance(fields, dict) or not fields or not set(fields) <= allowed:
            raise ServiceError('invalid_display_fields')
        if type(payload['revision']) is not int:
            raise ServiceError('invalid_revision')
        cleaned = {}
        for key, value in fields.items():
            if key != 'name' and (value is None or isinstance(value, str) and not value.strip()):
                cleaned[key] = None
            else:
                # Validate before stripping so control characters cannot be hidden.
                cleaned[key] = text(text(value, 80 if key == 'name' else 120).strip(), 80 if key == 'name' else 120)
        with self.registry.exclusive():
            value = self.registry.read()
            if payload['revision'] != value['revision']:
                raise ServiceError('revision_conflict')
            service = next((s for s in value['services'] if s['id'] == payload['id']), None)
            if not service:
                raise ServiceError('unknown_service')
            if service['default_profile_id'] != payload['profile_id']:
                raise ServiceError('revision_conflict')
            profile = next(p for p in value['profiles'] if p['id'] == payload['profile_id'])
            for key, label in cleaned.items():
                (service if key == 'name' else profile)[key] = label
            saved = self.registry.save_locked(value, payload['revision'])
        return dict(revision=saved['revision'])

    def reorder(self, payload):
        if not isinstance(payload, dict) or set(payload) != {'ids', 'revision'} or type(payload['revision']) is not int:
            raise ServiceError('invalid_order')
        ids = payload['ids']
        if not isinstance(ids, list) or len(ids) > 32 or any(not isinstance(s, str) for s in ids):
            raise ServiceError('invalid_order')
        with self.registry.exclusive():
            value = self.registry.read()
            services = {s['id']: s for s in value['services']}
            if len(ids) != len(services) or set(ids) != set(services):
                raise ServiceError('invalid_order')
            value['services'] = [services[sid] for sid in ids]
            saved = self.registry.save_locked(value, payload['revision'])
        return dict(revision=saved['revision'])

    def recent_events(self):
        names = {s['id']:s['name'] for s in self.registry.read()['services']}
        with self.op_lock:
            return [dict(id=o['id'],timestamp=o.get('finished_at', o.get('created_at', 0)),
                service_id=o['service_id'],service_name=names.get(o['service_id'],o['service_id']),
                action=o['action'],status=o['status'],code=o.get('code'),
                message=f"{o['service_id']} · {o['action']} · {o['status']}")
                for o in reversed(self.operations) if o['id'] not in self.activity_hidden or o['status'] in ('queued','running')]

    def clear_events(self, through):
        # Clear only the reviewed, finished display history. Keep recovery state intact.
        if isinstance(through,bool) or not isinstance(through,(int,float)) or not math.isfinite(through) or not 0 <= through <= time.time():
            raise ServiceError('invalid_activity_cutoff')
        with self.op_lock:
            existing={o['id'] for o in self.operations}
            candidates={o['id'] for o in self.operations if o['status'] not in ('queued','running') and o.get('finished_at',o.get('created_at',0))<=through}
            hidden=(self.activity_hidden | candidates) & existing
            atomic(self.activity_hidden_path,sorted(hidden))
            count=len(candidates-self.activity_hidden)
            self.activity_hidden=hidden
            return dict(cleared=count)

    def _command(self, action, unit):
        result = subprocess.run(['systemctl', '--user', '--no-block', action, '--', unit], capture_output=True, timeout=5)
        if result.returncode:
            raise ServiceError('manager_rejected')
        self.cached_at = 0

    def _wait(self, unit, desired, seconds):
        end = time.monotonic() + seconds
        consecutive = 0
        while time.monotonic() < end:
            state = process_state(system_states([unit]).get(unit, {}))
            if state == desired:
                consecutive += 1
                if desired != 'running' or consecutive >= 2:
                    return
            else:
                consecutive = 0
            if state == 'failed' and desired == 'stopped':
                fields=system_states([unit]).get(unit,{})
                if fields.get('MainPID','0') == '0': return
            if state in ('failed', 'unknown'):
                raise ServiceError('service_failed')
            time.sleep(1)
        raise ServiceError('process_timeout')

    def action(self, sid, action, profile_id=None, revision=None):
        if action not in ('start', 'stop', 'restart', 'select'):
            raise ServiceError('unsupported_action')
        guard = self.registry.exclusive()
        guard.__enter__()
        handed_off = False
        try:
            value = self.registry.read()
            if revision is not None and revision != value['revision']:
                raise ServiceError('revision_conflict')
            service = next((s for s in value['services'] if s['id'] == sid), None)
            if not service:
                raise ServiceError('unknown_service')
            profiles = [p for p in value['profiles'] if p['service_id'] == sid]
            old = next(p for p in profiles if p['id'] == service['default_profile_id'])
            target = next((p for p in profiles if p['id'] == (profile_id or old['id'])), None)
            if not target or not target['allow_control'] or not old['allow_control']:
                raise ServiceError('control_not_allowed')
            states = system_states([p['manager']['unit'] for p in value['profiles']])
            state = process_state(states.get(old['manager']['unit'], {}))
            if state in ('unknown', 'starting', 'stopping') or process_state(states.get(target['manager']['unit'], {})) == 'unknown':
                raise ServiceError('service_unavailable_or_busy')
            if action == 'select':
                if any(process_state(states.get(p['manager']['unit'], {})) not in ('stopped', 'failed') for p in profiles):
                    raise ServiceError('stop_before_switch')
                service['default_profile_id'] = target['id']
                self.registry.save_locked(value, value['revision'])
                self.cached_at = 0
                return dict(accepted=True, status='completed', code='profile_selected')
            if target['id'] != old['id']:
                raise ServiceError('select_profile_first')
            if action in ('start', 'restart'):
                if action in ('start','restart') and state in ('stopped','failed') and target['probe']:
                    with socket.socket() as sock:
                        # A stopped HTTP server can leave TIME_WAIT sockets. Reuse
                        # permits those while an actual listening socket still conflicts.
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        try:
                            sock.bind(('127.0.0.1', urlsplit(target['probe']['origin']).port))
                        except OSError:
                            raise ServiceError('probe_port_in_use') from None
                for p in value['profiles']:
                    if p['id'] == target['id'] or p['manager']['unit'] == target['manager']['unit']:
                        continue
                    if (p['service_id'] == sid or set(p['exclusive_groups']) & set(target['exclusive_groups'])) and process_state(states.get(p['manager']['unit'], {})) not in ('stopped', 'failed'):
                        raise ServiceError('conflicting_service_running')
            if action in ('stop', 'restart'):
                for p in value['profiles']:
                    if sid in p['uses_service_ids'] and process_state(states.get(p['manager']['unit'], {})) not in ('stopped', 'failed'):
                        raise ServiceError('dependent_service_running')
            op = dict(id=uuid.uuid4().hex, service_id=sid, action=action, profile_id=target['id'], status='queued', code='accepted', created_at=time.time())
            with self.op_lock:
                self.operations = (self.operations + [op])[-200:]
                atomic(self.operation_path, self.operations)
            worker = threading.Thread(target=self._execute, args=(guard, op, service, target), daemon=True, name='service-operation')
            worker.start()
            handed_off = True
            return copy.deepcopy(op)
        finally:
            if not handed_off:
                guard.__exit__(None, None, None)

    def _execute(self, guard, op, service, profile):
        try:
            self.update_operation(op, status='running')
            unit = profile['manager']['unit']
            if op['action'] in ('stop', 'restart'):
                self._command('stop', unit)
                self._wait(unit, 'stopped', 60)
            if op['action'] in ('start', 'restart'):
                deadline = time.monotonic() + profile['startup_timeout_seconds']
                fields=system_states([unit]).get(unit,{})
                if fields.get('ActiveState')=='failed':
                    if fields.get('MainPID','0')!='0': raise ServiceError('residual_process')
                    self._command('reset-failed',unit)
                self._command('start', unit)
                self._wait(unit, 'running', profile['startup_timeout_seconds'])
                if profile.get('startup_observer')=='tensorfold' or (profile['probe'] and service['adapter'] in ('comfyui', 'openai-compatible')):
                    while time.monotonic() < deadline:
                        state = process_state(system_states([unit]).get(unit, {}))
                        if state != 'running':
                            raise ServiceError('service_failed')
                        observed=self.observations.read(profile,system_states([unit]).get(unit,{})) if profile.get('startup_observer') else None
                        ready=probe(service['adapter'],profile,state)['readiness']=='ready' if profile['probe'] else bool(observed and observed['ready'])
                        if ready:
                            break
                        time.sleep(2)
                    else:
                        raise ServiceError('readiness_timeout_process_may_be_running')
            self.update_operation(op, status='completed', code='completed', finished_at=time.time())
        except Exception as error:
            # Exception strings can contain private paths or engine output: use a fixed code.
            code=str(error) if isinstance(error,ServiceError) else 'operation_failed_check_local_service'
            try:
                self.observations.clear()
                observed=self.observations.read(profile,system_states([profile['manager']['unit']]).get(profile['manager']['unit'],{}))
                code=observed['reason'] or code
            except Exception: pass
            self.update_operation(op,status='failed',code=code,finished_at=time.time())
        finally:
            self.cached_at = 0
            guard.__exit__(None, None, None)

    def discover(self):
        with self.cache_lock:
            if time.monotonic() - self.last_scan < 10:
                raise ServiceError('scan_cooldown')
            self.last_scan = time.monotonic()
            call = subprocess.run(['systemctl', '--user', 'list-unit-files', '--type=service', '--no-legend', '--no-pager'], capture_output=True, text=True, timeout=3)
            registered = {p['manager']['unit'] for p in self.registry.read()['profiles']}
            self.candidates = {}
            for line in call.stdout.splitlines()[:2048]:
                unit = line.split()[0] if line.split() else ''
                if any(k in unit.lower() for k in ('-install', '-update', '-download', '-tailnet-')):
                    continue
                if not UNIT.fullmatch(unit) or unit in registered or not any(k in unit.lower() for k in ('comfy', 'qwen', 'hermes', 'vllm', 'llama', 'ollama', 'lmstudio', 'tensorfold', 'gemma')):
                    continue
                key = uuid.uuid4().hex
                self.candidates[key] = unit
                if len(self.candidates) == 128:
                    break
            return dict(candidates=[dict(id=k, name=v, status='review_required') for k, v in self.candidates.items()], scope='user_systemd_units', expires_in=300)

    def register_candidate(self, candidate_id, revision):
        with self.cache_lock:
            unit = self.candidates.get(candidate_id)
            if not unit or time.monotonic() - self.last_scan > 300:
                raise ServiceError('scan_again')
            with self.registry.exclusive():
                value = self.registry.read()
                if any(p['manager']['unit'] == unit for p in value['profiles']):
                    raise ServiceError('already_registered')
                sid = 'service-' + uuid.uuid4().hex[:12]
                value['services'].append(dict(id=sid, name=unit.removesuffix('.service'), adapter='process', default_profile_id=sid))
                value['profiles'].append(dict(id=sid, service_id=sid, name='Default', manager=dict(type='systemd-user', unit=unit), allow_control=False))
                saved = self.registry.save_locked(value, revision)
                return dict(id=sid, revision=saved['revision'], controllable=False)


def main():
    parser = argparse.ArgumentParser(description='Local-only service registry. No service starts during validation/apply.')
    parser.add_argument('action', choices=['check', 'export', 'apply'])
    parser.add_argument('--data-dir', default=str(Path.home()/'.local/share/dgx-spark-control'))
    parser.add_argument('--file')
    parser.add_argument('--expected-revision', type=int)
    args = parser.parse_args()
    try:
        registry = Registry(args.data_dir)
        if args.action == 'export':
            print(json.dumps(registry.read(), ensure_ascii=False, indent=2))
        else:
            if not args.file or Path(args.file).stat().st_size > 262144:
                raise ServiceError('file_required_or_too_large')
            value = validate(json.loads(Path(args.file).read_text()))
            states = system_states([p['manager']['unit'] for p in value['profiles']])
            missing = sum(states.get(p['manager']['unit'], {}).get('LoadState') != 'loaded' for p in value['profiles'])
            if args.action == 'apply':
                if args.expected_revision is None or missing:
                    raise ServiceError('revision_required_or_missing_units')
                current = registry.read()
                if current != value and any(process_state(s) in ('starting', 'stopping') for s in states.values()):
                    raise ServiceError('service_transition_in_progress')
                value = registry.apply(value, args.expected_revision)
            print(json.dumps(dict(valid=True, services=len(value['services']), profiles=len(value['profiles']), missing_units=missing, revision=value['revision'])))
    except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired):
        parser.exit(2, 'Registry operation failed. Check schema, revision, units and any running dashboard operation.\n')


if __name__ == '__main__':
    main()
