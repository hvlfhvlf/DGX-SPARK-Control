"""Password-confirmed, single-use power requests; no power operation on GET."""
import hashlib
import json
import secrets
import subprocess
import threading
import time
from collections import deque

HELPER='/usr/lib/dgx-spark-control/packaging/power-helper.py'


def helper(action):
    if action not in ('check','reboot','poweroff'): raise ValueError('invalid_power_action')
    r=subprocess.run(['/usr/bin/python3',HELPER,action],capture_output=True,text=True,timeout=5)
    if r.returncode: raise ValueError('power_permission_or_inhibitor')
    return json.loads(r.stdout)


class Power:
    def __init__(self,config):
        self.config=config;self.lock=threading.Lock();self.pending={};self.failures=deque(maxlen=10);self.busy_until=0

    def status(self):
        try: return helper('check')
        except (ValueError,OSError,subprocess.SubprocessError): return dict(enabled=False,reason='local_setup_required')

    def prepare(self,session,action):
        if action not in ('reboot','poweroff'): raise ValueError('invalid_power_action')
        with self.lock:
            now=time.monotonic()
            if now<self.busy_until: raise ValueError('power_already_requested')
            status=self.status()
            if not status.get('enabled'): raise ValueError('power_permission_or_inhibitor')
            self.pending={k:v for k,v in self.pending.items() if v[2]>now and v[0]!=session}
            if len(self.pending)>=16: raise ValueError('power_confirmation_limit')
            token=secrets.token_urlsafe(32)
            fingerprint=hashlib.sha256(json.dumps(self.config.password,sort_keys=True).encode()).hexdigest()
            self.pending[token]=(session,action,now+60,self.config.value['spark_name'],fingerprint)
            return dict(confirmation=token,action=action,spark_name=self.config.value['spark_name'],expires_in=60)

    def confirm(self,session,data):
        with self.lock:
            now=time.monotonic();token=data.get('confirmation')
            if not isinstance(token,str): raise ValueError('power_confirmation_expired')
            item=self.pending.pop(token,None)
            fingerprint=hashlib.sha256(json.dumps(self.config.password,sort_keys=True).encode()).hexdigest()
            if not item or item[0]!=session or item[1]!=data.get('action') or item[2]<now or item[3]!=self.config.value['spark_name'] or item[4]!=fingerprint:
                raise ValueError('power_confirmation_expired')
            if now<self.busy_until: raise ValueError('power_already_requested')
            while self.failures and now-self.failures[0]>60: self.failures.popleft()
            if len(self.failures)>=5: raise ValueError('power_password_rate_limited')
            if not self.config.check_password(data.get('password')):
                self.failures.append(now);raise ValueError('power_password_incorrect')
            result=helper(item[1])
            if not result.get('accepted'): raise ValueError('power_permission_or_inhibitor')
            self.pending.clear();self.busy_until=now+120
            return dict(accepted=True,action=item[1])
