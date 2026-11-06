import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from spark_control.services import Registry, ServiceError
from spark_control.service_autostart import Autostart, simple_boot_unit
from test_services import fixture

class AutostartTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.registry=Registry(Path(self.tmp.name))
        self.registry.apply(fixture(),0);self.auto=Autostart(self.registry)
        self.enabled=False;self.other='disabled';self.linger='yes';self.calls=[]
        self.mock=patch('spark_control.service_autostart.command',side_effect=self.command);self.mock.start()
    def tearDown(self):self.mock.stop();self.tmp.cleanup()
    def command(self,args):
        self.calls.append(args)
        if args[0]=='loginctl':return SimpleNamespace(returncode=0,stdout=self.linger)
        if args[2]=='cat':return SimpleNamespace(returncode=0,stdout='[Install]\nWantedBy=default.target\n')
        if args[2]=='show':return SimpleNamespace(returncode=0,stdout='Id=test-one.service\nLoadState=loaded\nUnitFileState='+('enabled' if self.enabled else 'disabled')+'\n\nId=test-two.service\nLoadState=loaded\nUnitFileState='+self.other+'\n')
        self.enabled=args[2]=='enable';return SimpleNamespace(returncode=0,stdout='')
    def change(self,enabled=True,**extra):return self.auto.set(dict(id='test',profile_id='one',revision=1,enabled=enabled,**extra))
    def test_enable_disable_preserves_current_process(self):
        self.assertFalse(self.auto.status('test')['enabled'])
        self.assertTrue(self.change()['enabled']);self.assertFalse(self.change(False)['enabled'])
        self.assertEqual([c[2] for c in self.calls if c[0]=='systemctl' and c[2] in ('enable','disable')],['enable','disable'])
        self.assertFalse(any('--now' in c or any(x in c for x in ('start','stop','restart')) for c in self.calls))
        self.assertEqual(self.registry.read()['revision'],1)
    def test_get_and_idempotent_off_do_not_mutate(self):
        self.auto.status('test');self.change(False)
        self.assertFalse(any(c[2] in ('enable','disable') for c in self.calls if c[0]=='systemctl'))
    def test_stale_and_invalid_requests(self):
        for data in [dict(id='test',profile_id='one',revision=0,enabled=True),dict(id='test',profile_id='two',revision=1,enabled=True),dict(id='test',profile_id='one',revision=1,enabled='yes'),dict(id='unknown',enabled=True)]:
            with self.assertRaises(ServiceError):self.auto.set(data)
        self.assertFalse(self.enabled)
    def test_conflict_and_unknown_peer_block_enable(self):
        for state in ('enabled','enabled-runtime','unknown'):
            self.other=state
            with self.assertRaisesRegex(ServiceError,'autostart_conflict'):self.change()
        self.assertFalse(self.enabled)
    def test_linger_required_but_off_still_allowed(self):
        self.linger='no'
        with self.assertRaisesRegex(ServiceError,'autostart_linger_required'):self.change()
        self.enabled=True;self.assertFalse(self.change(False)['enabled'])
    def test_update_guard_and_read_only(self):
        (self.registry.directory/'service-update.lock').touch()
        self.assertTrue(self.auto.status('test')['maintenance'])
        with self.assertRaisesRegex(ServiceError,'update_in_progress'):self.change()
        (self.registry.directory/'service-update.lock').unlink()
        v=self.registry.read();v['profiles'][0]['allow_control']=False;self.registry.apply(v,1)
        self.assertFalse(self.auto.status('test')['editable'])
    def test_install_side_effects_rejected(self):
        for text in ('[Install]\nWantedBy=other.target','[Install]\nWantedBy=default.target\nAlso=other.service','[Install]\nWantedBy=default.target\nAlias=alias.service'):
            with patch('spark_control.service_autostart.command',return_value=SimpleNamespace(returncode=0,stdout=text)):
                self.assertFalse(simple_boot_unit('test-one.service'))
    def test_enable_failure_is_not_success(self):
        old=self.command
        def failed(args):
            if args[0]=='systemctl' and args[2]=='enable':return SimpleNamespace(returncode=1,stdout='private-error')
            return old(args)
        with patch('spark_control.service_autostart.command',side_effect=failed):
            with self.assertRaisesRegex(ServiceError,'autostart_change_failed'):self.change()
    def test_rebinding_enabled_profile_is_blocked(self):
        v=self.registry.read();v['services'][0]['default_profile_id']='two'
        with patch('spark_control.services.system_states',return_value={'test-one.service':dict(LoadState='loaded',ActiveState='inactive',UnitFileState='enabled')}):
            with self.assertRaisesRegex(ServiceError,'disable_autostart_before_rebinding'):self.registry.apply(v,1)
