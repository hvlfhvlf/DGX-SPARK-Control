"""Demand-driven inference telemetry. No prompts, inference requests or background jobs."""
import copy
import http.client
import json
import math
import re
import threading
import time
from collections import OrderedDict, deque
from urllib.parse import urlsplit
from .services import ServiceError, origin, system_states
from .local_http import connection


def number(value):
    return float(value) if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None


def fetch(base, path, accept='application/json'):
    """Fixed paths, bounded loopback response; never follows redirects or proxy env."""
    port = urlsplit(origin(base)).port
    conn = connection(port, timeout=.7)
    try:
        deadline = time.monotonic() + 1.3
        conn.request('GET', path, headers={'Accept': accept})
        response = conn.getresponse()
        if response.status != 200:
            raise ServiceError('metrics_unavailable')
        parts, size = [], 0
        while True:
            part = response.read1(16384)
            if not part:
                break
            size += len(part)
            if size > 262144 or time.monotonic() > deadline:
                raise ServiceError('metrics_limit')
            parts.append(part)
        return b''.join(parts).decode('utf-8')
    finally:
        conn.close()


def prometheus(raw):
    values = {}
    for line in raw.splitlines():
        match = re.fullmatch(r'([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{[^\n]*\})?\s+([^\s]+)(?:\s+[^\s]+)?', line)
        if not match:
            continue
        try:
            val = number(float(match[2]))
        except ValueError:
            continue
        if val is not None:
            values[match[1]] = values.get(match[1], 0) + val
    return values


def decode(raw, health=None):
    """Normalize only measured values; counter rates are calculated by the session tracker."""
    result = dict(engine='unsupported', output_total=None, input_total=None, live_total=None,
                  output_rate=None, input_rate=None, running=None, waiting=None,
                  context=None, model=None, run=None, rate_kind='poll-window', state='unknown')
    if raw.lstrip().startswith('{'):
        data = json.loads(raw)
        live = data.get('live', {})
        if not isinstance(live, dict) or live.get('state') not in ('idle', 'unloaded', 'reading', 'generating'):
            return result
        totals, engine = data.get('totals', {}), data.get('engine', {})
        result.update(engine='strata', state=live['state'], rate_kind='engine-window',
            output_rate=number(live.get('tok_s')) if live['state']=='generating' else (0 if live['state'] in ('idle','unloaded') else None),
            input_rate=number(live.get('prefill_tok_s_mean')) if live['state']=='reading' else None,
            output_total=number(totals.get('output_tokens')), input_total=number(totals.get('prompt_tokens')),
            running=number(live.get('running')), waiting=number(live.get('queued')),
            context=number(engine.get('max_context')), run=str(totals.get('since'))[:100] if totals.get('since') is not None else None)
        return result
    metrics = prometheus(raw)
    engine = next((e for e in ('tensorfold', 'strata', 'vllm') if any(k.startswith(e+':') for k in metrics)), None)
    if not engine:
        return result
    def get(*names):
        return next((metrics[engine+':'+n] for n in names if engine+':'+n in metrics), None)
    result.update(engine=engine, output_total=get('generation_tokens_total'), input_total=get('prompt_tokens_total'),
                  running=get('requests_running','num_requests_running'), waiting=get('requests_waiting','num_requests_waiting'),
                  run=metrics.get('process_start_time_seconds'))
    if engine=='tensorfold':
        running = get('generation_tokens_running')
        if running is not None and result['output_total'] is not None:
            result['live_total'] = running + result['output_total']
        live = (health or {}).get('live', {})
        if isinstance(live, dict):
            result['output_rate'] = number(live.get('decode_tokens_per_second'))
            result['input_rate'] = number(live.get('prefill_tokens_per_second'))
            if result['output_rate'] is not None:
                result['rate_kind'] = 'engine-window'
        if result['live_total'] is None and result['output_rate'] is None:
            result['rate_kind'] = 'completed-window'
    return result


class Inference:
    def __init__(self, services):
        self.services = services
        self.lock = threading.Lock()
        self.streams = OrderedDict()
        self.collections = 0

    def snapshot(self, service_id=None):
        listing = self.services.listing()
        registry = self.services.registry.read()
        llm_profiles={p['id'] for p in registry['profiles'] if p.get('startup_observer')=='tensorfold'}
        choices = [r for r in listing['services'] if r['adapter']=='openai-compatible' or r['profile_id'] in llm_profiles]
        selected = next((r for r in choices if r['id']==service_id), None) if service_id else next((r for r in choices if r['state']=='running'), choices[0] if choices else None)
        result = dict(services=choices, selected=selected['id'] if selected else None, current=None, history=[], status='no_service')
        if not selected:
            return result
        profile = next((p for p in registry['profiles'] if p['id']==selected['profile_id']), None)
        if not profile or not profile['probe']:
            result['status']='not_configured'
            return result
        key = (profile['id'], profile['probe']['origin'])
        with self.lock:
            stream = self.streams.setdefault(key, dict(at=0, previous=None, history=deque(maxlen=720), model=None, model_at=0))
            self.streams.move_to_end(key)
            while len(self.streams)>4:
                self.streams.popitem(last=False)
            now = time.monotonic()
            if now-stream['at']>=5:
                self.collections += 1
                timestamp = time.time()
                sample = dict(timestamp=timestamp, output_rate=None, input_rate=None, output_total=None, input_total=None,
                              running=None, waiting=None, context=None, engine=None, model=None, rate_kind=None)
                status='stopped' if selected['state'] not in ('running','starting') else 'unavailable'
                if selected['state']=='running':
                    try:
                        base = profile['probe']['origin']
                        raw = fetch(base, '/metrics', 'text/plain, application/json')
                        health = None
                        if 'tensorfold:' in raw:
                            try:
                                health = json.loads(fetch(base, '/health'))
                            except (ValueError, OSError, http.client.HTTPException):
                                pass
                        if 'strata:' in raw:
                            raw = fetch(base, '/metrics')
                        reading = decode(raw, health)
                        fields = system_states([profile['manager']['unit']]).get(profile['manager']['unit'], {})
                        invocation = fields.get('InvocationID')
                        if now-stream['model_at']>=30 or stream.get('invocation')!=invocation:
                            stream['model_at']=now
                            # Metadata from a previous engine run must not survive a failed refresh.
                            stream['context']=None
                            try:
                                data = json.loads(fetch(base, '/v1/models')).get('data', [])
                                model = data[0].get('id') if len(data)==1 and isinstance(data[0],dict) else None
                                # Server model identifiers can contain private filesystem paths.
                                stream['model'] = model[:120] if isinstance(model,str) and not model.startswith(('/', '~', '\\')) and not any(ord(c)<32 for c in model) else None
                                if len(data)==1 and isinstance(data[0],dict):
                                    context = number(data[0].get('max_model_len'))
                                    if context is not None:
                                        reading['context'] = context
                                stream['context']=reading['context']
                            except (ValueError, OSError, http.client.HTTPException, TypeError, AttributeError):
                                stream['model']=None
                        reading['model']=stream['model']
                        reading['context']=reading['context'] or stream.get('context')
                        identity=(invocation, reading['engine'], reading['model'], reading['run'])
                        previous=stream['previous']
                        dt=now-stream['at']
                        same=previous and stream.get('identity')==identity and 0<dt<=15
                        if same:
                            for field in ('output_total','input_total'):
                                if reading[field] is not None and previous[field] is not None and reading[field]<previous[field]:
                                    same=False
                        if stream.get('identity')!=identity:
                            stream['history'].clear()
                        if same and reading['live_total'] is not None and previous['live_total'] is not None:
                            reading['live_total']=max(reading['live_total'],previous['live_total'])
                        if same:
                            for rate, field in [('output_rate','live_total' if reading['live_total'] is not None else 'output_total'),('input_rate','input_total')]:
                                # Input throughput is admitted tokens / wall time, not prefill compute speed.
                                if reading[rate] is None and reading[field] is not None and previous[field] is not None:
                                    reading[rate]=max(0,(reading[field]-previous[field])/dt)
                        # Keep input graph comparable across engines: counter / wall time only.
                        reading['input_rate']=max(0,(reading['input_total']-previous['input_total'])/dt) if same and reading['input_total'] is not None and previous['input_total'] is not None else None
                        stream.update(previous=reading.copy(), identity=identity, invocation=invocation)
                        sample.update({k:reading[k] for k in sample if k in reading})
                        status='unsupported' if reading['engine']=='unsupported' else 'ok'
                    except (ValueError, OSError, http.client.HTTPException, TypeError, AttributeError, KeyError):
                        stream['previous']=None
                else:
                    stream['previous']=None
                stream.update(at=now, current=sample, status=status)
                stream['history'].append(sample)
            result.update(status=stream['status'],current=copy.deepcopy(stream['current']),history=list(stream['history']))
        return result
