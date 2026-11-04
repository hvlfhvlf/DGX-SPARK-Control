import copy
import importlib.util
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from spark_control.power import Power
from spark_control.startup import Observations, parse
from spark_control.programs import Programs
from spark_control.services import Services, ServiceError
from test_services import fixture


class StartupTests(unittest.TestCase):
    def test_real_layers_are_not_readiness(self):
        result=parse(['[start.sh] Ready: image', 'info: flashnext: rank 1/1 loaded layer 48/48'],True)
        self.assertEqual(result['current'],48);self.assertFalse(result['ready'])
        self.assertTrue(parse(['[tensorfold] serving Test at http://127.0.0.1:8888'],True)['ready'])
        self.assertIsNone(parse(['info: flashnext: rank 1/1 loaded layer 49/48'],True)['current'])
        self.assertIsNone(parse(['info: flashnext: rank 1/1 loaded layer 1/48'])['current'])

    def test_error_projection_has_no_raw_log(self):
        result=parse(['private /private/example token=secret: CUDA memory budget fits no stream'])
        self.assertEqual(result['reason'],'memory_insufficient')
        self.assertNotIn('secret',json.dumps(result))
        self.assertEqual(parse(['Only 90 GiB memory available'])['reason'],'memory_insufficient')

    def test_invocation_cache_and_expiry(self):
        observer=Observations();profile={'manager':{'unit':'test.service'},'startup_observer':'tensorfold'}
        with patch('spark_control.startup.journal',return_value=['info: flashnext: rank 1/1 loaded layer 4/48']) as log:
            self.assertEqual(observer.read(profile,{'InvocationID':'a'*32})['current'],4)
            observer.read(profile,{'InvocationID':'a'*32});self.assertEqual(log.call_count,1)
            self.assertIsNone(observer.read(profile,{'InvocationID':'b'*32},False)['current'])
            observer.clear();self.assertEqual(observer.cache,{})


class RecoveryTests(unittest.TestCase):
    def test_failed_start_resets_once_and_checks_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            svc=Services(SimpleNamespace(directory=Path(tmp),value={'models':[]}));svc.registry.apply(fixture(),0)
            profile=svc.registry.read()['profiles'][0];profile['startup_observer']='tensorfold'
            op={'id':'op','service_id':'test','action':'start','status':'queued'};svc.operations=[op]
            state={'LoadState':'loaded','ActiveState':'failed','MainPID':'0'};commands=[]
            def command(action,unit):
                commands.append(action)
                if action=='start':state['ActiveState']='active'
            guard=SimpleNamespace(__exit__=lambda *a:None)
            with patch('spark_control.services.system_states',side_effect=lambda u:{u[0]:dict(state)}),patch.object(svc,'_command',side_effect=command),patch.object(svc,'_wait'),patch.object(svc.observations,'read',return_value={'ready':True}):
                svc._execute(guard,op,{'adapter':'process'},profile)
            self.assertEqual(commands,['reset-failed','start']);self.assertEqual(op['status'],'completed')

    def test_failed_residual_process_not_restarted(self):
        with tempfile.TemporaryDirectory() as tmp:
            svc=Services(SimpleNamespace(directory=Path(tmp),value={'models':[]}));svc.registry.apply(fixture(),0)
            op={'id':'op','service_id':'test','action':'start','status':'queued'};svc.operations=[op]
            with patch('spark_control.services.system_states',return_value={'test-one.service':{'LoadState':'loaded','ActiveState':'failed','MainPID':'12'}}),patch.object(svc,'_command') as command,patch.object(svc.observations,'read',return_value={'reason':None}):
                svc._execute(SimpleNamespace(__exit__=lambda *a:None),op,{'adapter':'process'},svc.registry.read()['profiles'][0])
            command.assert_not_called();self.assertEqual(op['code'],'residual_process')


class PowerTests(unittest.TestCase):
    def setUp(self):
        self.config=SimpleNamespace(password={'hash':'test'},value={'spark_name':'Test'},check_password=lambda p:p=='test-password')
        self.power=Power(self.config)
        self.mock=patch('spark_control.power.helper',side_effect=lambda action:{'enabled':True} if action=='check' else {'accepted':True})
        self.helper=self.mock.start();self.addCleanup(self.mock.stop)

    def prepared(self):
        v=self.power.prepare('session','reboot');return dict(action='reboot',confirmation=v['confirmation'],password='test-password')

    def test_two_step_password_and_single_use(self):
        with self.assertRaises(ValueError):self.power.confirm('session',dict(action='reboot',password='test-password'))
        data=self.prepared();self.assertEqual([c.args[0] for c in self.helper.call_args_list],['check'])
        self.assertTrue(self.power.confirm('session',data)['accepted'])
        with self.assertRaises(ValueError):self.power.confirm('session',data)
        self.assertEqual([c.args[0] for c in self.helper.call_args_list].count('reboot'),1)

    def test_session_action_name_password_revision_expiry_binding(self):
        for mutation in ('session','action','name','password','expired'):
            self.power=Power(self.config);data=self.prepared();session='session'
            if mutation=='session':session='different'
            if mutation=='action':data['action']='poweroff'
            if mutation=='name':self.config.value['spark_name']+='x'
            if mutation=='password':self.config.password['hash']+='x'
            if mutation=='expired':
                k=data['confirmation'];item=list(self.power.pending[k]);item[2]=0;self.power.pending[k]=tuple(item)
            with self.assertRaisesRegex(ValueError,'power_confirmation_expired'):self.power.confirm(session,data)
        self.assertFalse(any(c.args[0]!='check' for c in self.helper.call_args_list))

    def test_wrong_password_consumes_confirmation_and_throttles(self):
        for i in range(5):
            data=self.prepared();data['password']='wrong'
            with self.assertRaisesRegex(ValueError,'power_password_incorrect'):self.power.confirm('session',data)
            with self.assertRaisesRegex(ValueError,'power_confirmation_expired'):self.power.confirm('session',data)
        with self.assertRaisesRegex(ValueError,'power_password_rate_limited'):self.power.confirm('session',self.prepared())
        self.assertFalse(any(c.args[0]!='check' for c in self.helper.call_args_list))

    def test_disabled_and_unknown_action_fail_closed(self):
        self.helper.return_value={'enabled':False};self.helper.side_effect=None
        with self.assertRaises(ValueError):self.prepared()
        with self.assertRaises(ValueError):self.power.prepare('session','shell')


class PowerDispatchTests(unittest.TestCase):
    def setUp(self):
        path=Path(__file__).resolve().parents[1]/'packaging/power-helper.py'
        spec=importlib.util.spec_from_file_location('power_helper_test',path)
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)

    def test_fixed_timer_dispatch_and_execution_are_mocked(self):
        m=self.module
        with patch.object(m.os,'getuid',return_value=1000),patch.object(m,'check',return_value=True),patch.object(m,'query',return_value='yes'),patch.object(m.subprocess,'run') as run,patch.object(m.sys,'argv',['helper','reboot']):
            self.assertEqual(m.main(),0)
            args=run.call_args.args[0]
            self.assertIn('--user',args);self.assertIn('--property=NoNewPrivileges=yes',args)
            self.assertEqual(args[-1],'execute-reboot');self.assertNotIn('PowerOff',args)
        with patch.object(m.os,'getuid',return_value=1000),patch.object(m,'check',return_value=False),patch.object(m.subprocess,'run') as run,patch.object(m.sys,'argv',['helper','execute-reboot']):
            self.assertEqual(m.main(),1);run.assert_not_called()

    def test_blockers_and_other_users_fail_closed(self):
        m=self.module
        with patch.object(m.os,'getuid',return_value=1000),patch.object(m,'query',return_value=[['shutdown','app','busy','block',1000,1]]):
            self.assertFalse(m.check())
        with patch.object(m.os,'getuid',return_value=1000),patch.object(m,'query',side_effect=[[],[['1',1001,'other','','']]]):
            self.assertFalse(m.check())


class ProgramTests(unittest.TestCase):
    def test_cache_counter_reset_and_pid_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'uptime').write_text('1000 0');p=root/'42';p.mkdir();(p/'cgroup').write_text('0::/user@1000.service/app/test.service')
            def stat(ticks,start=100):
                fields=['0']*22;fields[0]='S';fields[11]=str(ticks);fields[19]=str(start);fields[21]='20';(p/'stat').write_text('42 (test name) '+' '.join(fields))
            stat(100);programs=Programs(root)
            with patch('spark_control.programs.time.monotonic',return_value=100):first=programs.snapshot()
            self.assertIsNone(first['rows'][0]['cpu']);self.assertEqual(first['rows'][0]['group'],'test.service')
            with patch('spark_control.programs.time.monotonic',return_value=101):self.assertIs(programs.snapshot(),first)
            stat(200)
            with patch('spark_control.programs.time.monotonic',return_value=106):self.assertGreater(programs.snapshot()['rows'][0]['cpu'],0)
            stat(10,200)
            with patch('spark_control.programs.time.monotonic',return_value=112):self.assertIsNone(programs.snapshot()['rows'][0]['cpu'])
            self.assertNotIn('cmdline',json.dumps(first))


if __name__=='__main__':unittest.main()
