"""Review and register existing user services. Never creates or executes shell commands."""
import subprocess
import threading
import time
import uuid
from pathlib import Path
from .services import ServiceError, UNIT, ADAPTERS, origin, text, probe, process_state, system_states


class Connections:
    def __init__(self, services):
        self.services = services
        self.lock = threading.Lock()
        self.candidates, self.checks = {}, {}
        self.scanned = 0

    def discover(self):
        with self.lock:
            if self.scanned and time.monotonic()-self.scanned<10:
                raise ServiceError('scan_cooldown')
            call=subprocess.run(['systemctl','--user','list-unit-files','--type=service','--no-legend','--no-pager'],capture_output=True,text=True,timeout=3)
            if call.returncode:
                raise ServiceError('discovery_failed')
            self.candidates={}
            registered={p['manager']['unit'] for p in self.services.registry.read()['profiles']}
            units=[]
            for line in call.stdout.splitlines()[:2048]:
                unit=line.split()[0] if line.split() else ''
                if UNIT.fullmatch(unit) and not unit.endswith('@.service') and not unit.startswith('dgx-spark-control') and not any(k in unit.lower() for k in ('-install','-update','-download')) and unit not in units:
                    units.append(unit)
            units.sort(key=lambda u:(not any(k in u.lower() for k in ('qwen','comfy','hermes','vllm','strata','llama','ollama','tensorfold','lmstudio','gemma')),u))
            states=system_states(units[:128])
            rows=[]
            for unit in units[:128]:
                fields=states.get(unit,{})
                fragment=Path(fields.get('FragmentPath') or '/')
                custom=fragment.is_relative_to(Path.home()) or fragment.is_relative_to('/etc/systemd/user')
                known=any(k in unit.lower() for k in ('qwen','comfy','hermes','vllm','strata','llama','ollama','tensorfold','lmstudio','gemma'))
                if fields.get('LoadState')!='loaded' or not (custom or known or unit in registered):
                    continue
                candidate=uuid.uuid4().hex
                self.candidates[candidate]=unit
                rows.append(dict(id=candidate,name=unit,state=process_state(states.get(unit,{})),registered=unit in registered))
            self.scanned=time.monotonic()
            return dict(candidates=rows,scope='user_systemd_units',truncated=len(units)>128)

    def settings(self, sid):
        value=self.services.registry.read()
        service=next((s for s in value['services'] if s['id']==sid),None)
        if not service:
            raise ServiceError('unknown_service')
        profile=next(p for p in value['profiles'] if p['id']==service['default_profile_id'])
        return dict(revision=value['revision'],service_id=sid,name=service['name'],adapter=service['adapter'],
                    port=int(profile['probe']['origin'].rsplit(':',1)[1]) if profile['probe'] else None,
                    allow_control=profile['allow_control'],open_url=profile['open_url'] or '',
                    profile_name=profile['name'],unit=profile['manager']['unit'])

    def _prepare(self, data):
        allowed={'service_id','candidate_id','parent_id','name','profile_name','adapter','port','allow_control','open_url','revision'}
        if not isinstance(data,dict) or set(data)-allowed or type(data.get('revision')) is not int:
            raise ServiceError('invalid_connection')
        value=self.services.registry.read()
        if value['revision']!=data['revision']:
            raise ServiceError('revision_conflict')
        sid=data.get('service_id')
        service=next((s for s in value['services'] if s['id']==sid),None) if sid else None
        if sid and not service:
            raise ServiceError('unknown_service')
        if service:
            profile=next(p for p in value['profiles'] if p['id']==service['default_profile_id'])
            unit=profile['manager']['unit']
        else:
            unit=self.candidates.get(data.get('candidate_id'))
            if not unit or time.monotonic()-self.scanned>300:
                raise ServiceError('scan_again')
            if any(p['manager']['unit']==unit for p in value['profiles']):
                raise ServiceError('already_registered')
            parent=data.get('parent_id')
            service=next((s for s in value['services'] if s['id']==parent),None) if parent else None
            if parent and not service:
                raise ServiceError('unknown_service')
            sid=parent or 'service-'+uuid.uuid4().hex[:12]
            profile=dict(id='profile-'+uuid.uuid4().hex[:12],service_id=sid,manager=dict(type='systemd-user',unit=unit))
            if not service:
                service=dict(id=sid,default_profile_id=profile['id'])
                value['services'].append(service)
            value['profiles'].append(profile)
        adapter=data.get('adapter')
        if adapter not in ADAPTERS or type(data.get('allow_control')) is not bool:
            raise ServiceError('invalid_connection')
        if data.get('parent_id') and service['adapter']!=adapter:
            raise ServiceError('adapter_mismatch')
        port=data.get('port')
        if port is not None and type(port) is not int:
            raise ServiceError('invalid_probe_port')
        endpoint=origin('http://127.0.0.1:'+str(port)) if port is not None else None
        if adapter in ('openai-compatible','comfyui') and not endpoint:
            raise ServiceError('probe_required')
        service.update(name=text(data.get('name')),adapter=adapter)
        # Preserve conflict/dependency and display metadata when editing a binding.
        groups=[g for g in profile.get('exclusive_groups',[]) if not g.startswith('port:')]
        profile.update(name=text(data.get('profile_name','Default')),probe=dict(origin=endpoint) if endpoint else None,
                       allow_control=data['allow_control'],open_url=data.get('open_url') or None,exclusive_groups=groups)
        from .services import validate
        value=validate(value)
        profile=next(p for p in value['profiles'] if p['id']==profile['id'])
        fields=system_states([unit]).get(unit,{})
        if fields.get('LoadState')!='loaded':
            raise ServiceError('service_not_loaded')
        return value,profile,adapter,fields

    def check(self, data):
        with self.lock:
            value,profile,adapter,fields=self._prepare(data)
            state=process_state(fields)
            observation=probe(adapter,profile,state)
            ticket=uuid.uuid4().hex
            now=time.monotonic()
            self.checks={k:v for k,v in self.checks.items() if now-v['at']<120}
            if len(self.checks)>=16:
                self.checks.pop(next(iter(self.checks)))
            self.checks[ticket]=dict(at=now,value=value,revision=data['revision'],unit=profile['manager']['unit'])
            return dict(ticket=ticket,state=state,readiness=observation['readiness'],unit=profile['manager']['unit'],
                        allow_control=profile['allow_control'],service_id=profile['service_id'])

    def save(self, ticket):
        with self.lock:
            item=self.checks.pop(ticket,None) if isinstance(ticket,str) else None
            if not item or time.monotonic()-item['at']>120:
                raise ServiceError('check_again')
            if system_states([item['unit']]).get(item['unit'],{}).get('LoadState')!='loaded':
                raise ServiceError('service_not_loaded')
            saved=self.services.registry.apply(item['value'],item['revision'])
            self.services.cached_at=0
            return dict(saved=True,revision=saved['revision'])
