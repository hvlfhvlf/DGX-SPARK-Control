"""Bounded local startup observations. Only fixed codes and counters leave this module."""
import json
import os
import re
import select
import subprocess
import time
import threading


def journal(unit, invocation):
    if not re.fullmatch(r'[a-f0-9]{32}', invocation or ''):
        return []
    args = ['journalctl', '--user', '-u', unit, '_SYSTEMD_INVOCATION_ID='+invocation,
            '--grep=loaded layer|^\\[tensorfold\\] serving |cuda memory budget|gib memory available|out of memory|address already in use|no such file or directory',
            '--case-sensitive=no', '-n', '160', '--no-pager', '-o', 'json', '--output-fields=MESSAGE']
    chunks = bytearray()
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as child:
        deadline = time.monotonic()+1.5
        try:
            while len(chunks)<131072 and time.monotonic()<deadline:
                if not select.select([child.stdout], [], [], max(0, deadline-time.monotonic()))[0]:
                    break
                part=os.read(child.stdout.fileno(), min(16384,131072-len(chunks)))
                if not part: break
                chunks.extend(part)
        finally:
            if child.poll() is None: child.kill()
            child.wait()
    messages=[]
    for line in chunks.splitlines():
        try:
            message=json.loads(line).get('MESSAGE')
            if isinstance(message,str): messages.append(message[:8192])
        except (ValueError, AttributeError): pass
    return messages


def parse(messages, tensorfold=False):
    result=dict(phase='initializing', current=None, total=None, ready=False, reason=None)
    for line in messages:
        lower=line.lower()
        if 'cuda memory budget fits no stream' in lower or re.search(r'only \d+(?:\.\d+)? gib memory available',lower) or 'out of memory' in lower:
            result['reason']='memory_insufficient'
        elif 'address already in use' in lower: result['reason']='probe_port_in_use'
        elif 'no such file or directory' in lower: result['reason']='required_file_missing'
        if tensorfold:
            match=re.search(r'info: \w+: rank 1/1 loaded layer (\d+)/(\d+)',line)
            if match:
                current,total=map(int,match.groups())
                if 0<=current<=total<=10000 and total:
                    result.update(phase='weights',current=current,total=total)
            if re.match(r'^\[tensorfold\] serving .+ at http://',line):
                result.update(phase='serving',ready=True)
    return result


class Observations:
    def __init__(self): self.cache={};self.lock=threading.RLock()

    def clear(self):
        with self.lock: self.cache.clear()

    def read(self, profile, fields, collect=True):
        with self.lock: return self._read(profile, fields, collect)

    def _read(self, profile, fields, collect=True):
        unit=profile['manager']['unit'];invocation=fields.get('InvocationID','')
        key=(unit,invocation); now=time.monotonic()
        old=self.cache.get(key)
        if not collect and not old: return dict(parse([]),elapsed=None,invocation=invocation)
        if collect and (not old or now-old[0]>=5):
            try: data=parse(journal(unit,invocation),profile.get('startup_observer')=='tensorfold')
            except (OSError, subprocess.SubprocessError): data=parse([])
            if old and data['current'] is None and not data['reason']:
                data.update({k:old[1][k] for k in ('phase','current','total','ready')})
            self.cache[key]=(now,data)
            if len(self.cache)>64: self.cache.pop(next(iter(self.cache)))
        data=dict(self.cache[key][1])
        if fields.get('Result')=='start-limit-hit': data['reason']=data['reason'] or 'start_rate_limited'
        start=int(fields.get('ExecMainStartTimestampMonotonic','0') or 0)/1e6
        data['elapsed']=max(0,int(now-start)) if start else None
        data['invocation']=invocation  # internal only; strip before returning an API projection
        return data
