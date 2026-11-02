import copy
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from spark_control.services import Registry, ServiceError, Services, local_json, probe, validate


def fixture():
    return dict(registry_schema=1, revision=0, services=[dict(id='test', name='Test', adapter='process', default_profile_id='one')],
        profiles=[dict(id='one', service_id='test', name='One', manager=dict(type='systemd-user', unit='test-one.service'), allow_control=True),
                  dict(id='two', service_id='test', name='Two', manager=dict(type='systemd-user', unit='test-two.service'), allow_control=True)], assets=[])


def states(units, running=()):
    return {u:dict(Id=u, LoadState='loaded', ActiveState='active' if u in running else 'inactive') for u in units}


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = SimpleNamespace(directory=Path(self.tmp.name), value={'models': []})
        self.svc = Services(self.config)
        self.svc.registry.apply(fixture(), 0)

    def tearDown(self):
        self.tmp.cleanup()

    def test_private_atomic_revision_and_cross_instance_lock(self):
        value = self.svc.registry.read()
        self.assertEqual(value['revision'], 1)
        self.assertEqual(self.svc.registry.path.stat().st_mode & 0o777, 0o600)
        with self.assertRaisesRegex(ServiceError, 'revision_conflict'):
            self.svc.registry.apply(value, 0)
        with self.svc.registry.exclusive():
            with self.assertRaisesRegex(ServiceError, 'operation_in_progress'):
                self.svc.registry.apply(value, 1)
        self.assertEqual(self.svc.registry.read(), value)

    def test_reject_commands_remote_urls_and_duplicate_units(self):
        for unit in ['../evil.service', 'x.service;touch x', '-bad.service', 'dgx-spark-control.service']:
            value=fixture();value['profiles'][0]['manager']['unit']=unit
            with self.assertRaises(ServiceError):validate(value)
        for base in ['http://example.com:8188','http://127.0.0.1:8188/private','http://secret@127.0.0.1:8188','http://127.0.0.1:22','https://127.0.0.1:8188']:
            value=fixture();value['profiles'][0]['probe']={'origin':base}
            with self.assertRaises(ServiceError):validate(value)
        value=fixture();value['profiles'][0]['open_url']='https://user:secret@example.com'
        with self.assertRaises(ServiceError):validate(value)

    def test_legacy_migration_preserves_auth_and_never_starts(self):
        with tempfile.TemporaryDirectory() as tmp, patch('spark_control.services.subprocess.run') as run:
            registry=Registry(tmp,[dict(id='legacy',name='Legacy',service='legacy.service',allow_control=True)])
            self.assertEqual(registry.read()['profiles'][0]['manager']['unit'],'legacy.service')
            run.assert_not_called()

    def test_listing_cache_projection_and_unsupported_readiness(self):
        with patch('spark_control.services.system_states',side_effect=lambda u:states(u,['test-one.service'])) as collect:
            first=self.svc.listing();second=self.svc.listing()
            self.assertEqual(collect.call_count,1)
            self.assertEqual(first,second)
            row=first['services'][0]
            self.assertEqual(row['readiness'],'unsupported')
            self.assertNotIn('manager',row)
            self.assertNotIn('probe',row)

    def test_readiness_does_not_leak_workflows_or_model_paths(self):
        p=validate(fixture())['profiles'][0];p['probe']={'origin':'http://127.0.0.1:8188'}
        with patch('spark_control.services.local_json',side_effect=[{'system':{},'devices':[]},{'queue_running':[['private prompt','/private/model']], 'queue_pending':[]} ]):
            result=probe('comfyui',p,'running')
            self.assertEqual(result['running_jobs'],1)
            self.assertNotIn('private',json.dumps(result))
        with patch('spark_control.services.local_json',return_value={'data':[{'id':'/private/path'}]}):
            result=probe('openai-compatible',p,'running')
            self.assertEqual(result['model_count'],1)
            self.assertNotIn('/private',json.dumps(result))
        with patch('spark_control.services.local_json',side_effect=OSError('sensitive exception')):
            self.assertEqual(probe('comfyui',p,'running')['readiness'],'unreachable')

    def test_select_requires_stop_and_does_not_start(self):
        with patch('spark_control.services.system_states',side_effect=lambda u:states(u,['test-one.service'])), patch.object(self.svc,'_command') as command:
            with self.assertRaisesRegex(ServiceError,'stop_before_switch'):
                self.svc.action('test','select','two',1)
            command.assert_not_called()
        with patch('spark_control.services.system_states',side_effect=states), patch.object(self.svc,'_command') as command:
            self.svc.action('test','select','two',1)
            command.assert_not_called()
            self.assertEqual(self.svc.registry.read()['services'][0]['default_profile_id'],'two')

    def test_registry_cannot_rebind_running_selected_service(self):
        value=self.svc.registry.read();value['services'][0]['default_profile_id']='two'
        with patch('spark_control.services.system_states',side_effect=lambda u:states(u,['test-one.service'])):
            with self.assertRaisesRegex(ServiceError,'stop_before_rebinding'):
                self.svc.registry.apply(value,1)

    def test_duplicate_operation_and_restart_order(self):
        started=threading.Event();release=threading.Event();commands=[]
        def command(action,unit):
            commands.append(action)
            started.set();release.wait(2)
        with patch('spark_control.services.system_states',side_effect=states), patch.object(self.svc,'_command',side_effect=command), patch.object(self.svc,'_wait'):
            op=self.svc.action('test','restart',revision=1)
            self.assertTrue(started.wait(2))
            with self.assertRaisesRegex(ServiceError,'operation_in_progress'):
                self.svc.action('test','start',revision=1)
            release.set()
            deadline=time.monotonic()+3
            while self.svc.operations[-1]['status'] in ('queued','running') and time.monotonic()<deadline:time.sleep(.01)
            self.assertEqual(self.svc.operations[-1]['status'],'completed')
            self.assertEqual(commands,['stop','start'])

    def test_readonly_and_unknown_actions_never_run(self):
        with patch('spark_control.services.system_states',side_effect=states),patch.object(self.svc,'_command') as command:
            for sid,action in [('unregistered','start'),('test','shell')]:
                with self.assertRaises(ServiceError):self.svc.action(sid,action)
            value=self.svc.registry.read();value['profiles'][0]['allow_control']=False;self.svc.registry.apply(value,1)
            with self.assertRaises(ServiceError):self.svc.action('test','start')
            command.assert_not_called()

    def test_discovery_review_only_and_expiry(self):
        output=SimpleNamespace(stdout='comfy-demo.service enabled\nother.service enabled\n')
        with patch('spark_control.services.subprocess.run',return_value=output):
            found=self.svc.discover()['candidates']
            self.assertEqual(len(found),1)
            registration=self.svc.register_candidate(found[0]['id'],1)
            self.assertFalse(registration['controllable'])
            self.assertFalse(self.svc.registry.read()['profiles'][-1]['allow_control'])
            with self.assertRaises(ServiceError):self.svc.register_candidate('forged',2)

    def test_restart_reconciles_without_replaying(self):
        self.svc.operations=[dict(id='test',service_id='test',status='running',action='start')]
        from spark_control.services import atomic
        atomic(self.svc.operation_path,self.svc.operations)
        with patch('spark_control.services.subprocess.run') as run:
            restored=Services(self.config)
            self.assertEqual(restored.operations[0]['status'],'interrupted')
            run.assert_not_called()


if __name__=='__main__':unittest.main()
