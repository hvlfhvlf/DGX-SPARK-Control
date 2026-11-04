import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from spark_control.config import Config
from spark_control.services import Services, ServiceError
from spark_control.connections import Connections


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.svc=Services(Config(self.tmp.name));self.manager=Connections(self.svc)
        self.patch=patch('spark_control.connections.system_states',side_effect=lambda units:{u:dict(Id=u,LoadState='loaded',ActiveState='inactive',FragmentPath=str(Path.home()/'.config/systemd/user'/u) if u!='dbus.service' else '/usr/lib/systemd/user/dbus.service') for u in units});self.patch.start()
        self.registry_patch=patch('spark_control.services.system_states',side_effect=lambda units:{u:dict(Id=u,LoadState='loaded',ActiveState='inactive') for u in units});self.registry_patch.start()
    def tearDown(self):
        self.patch.stop();self.registry_patch.stop();self.tmp.cleanup()
    def candidate(self):
        with patch('spark_control.connections.subprocess.run',return_value=SimpleNamespace(returncode=0,stdout='custom-ai.service disabled\ndgx-spark-control.service enabled\napp-template@.service static\nmodel-install.service disabled\ndbus.service enabled\n')) as run:
            rows=self.manager.discover()['candidates'];self.assertEqual(len(rows),1)
            self.assertEqual(run.call_args.args[0][2],'list-unit-files')
        return dict(candidate_id=rows[0]['id'],name='AI',profile_name='Default',adapter='openai-compatible',port=18888,allow_control=True,revision=0,open_url='')
    def test_review_save_control_and_replay(self):
        data=self.candidate();checked=self.manager.check(data)
        self.assertEqual(self.svc.registry.read()['services'],[])
        self.assertEqual(checked['readiness'],'unknown')
        self.manager.save(checked['ticket'])
        self.assertTrue(self.svc.registry.read()['profiles'][0]['allow_control'])
        with self.assertRaises(ServiceError):self.manager.save(checked['ticket'])
    def test_no_commands_or_arbitrary_unit_and_conflicting_review(self):
        data=self.candidate()
        for extra in ({'command':'rm anything'},{'unit':'unreviewed.service'}):
            with self.assertRaises(ServiceError):self.manager.check(dict(data,**extra))
        for port in (22,'18888/path','18888@evil',True):
            with self.assertRaises(ValueError):self.manager.check(dict(data,port=port))
        first=self.manager.check(data);second=self.manager.check(data)
        self.manager.save(first['ticket'])
        with self.assertRaisesRegex(ServiceError,'revision_conflict'):self.manager.save(second['ticket'])
    def test_edit_preserves_launch_metadata(self):
        data=self.candidate();checked=self.manager.check(data);self.manager.save(checked['ticket'])
        value=self.svc.registry.read();value['profiles'][0]['model_name']='Verified model'
        self.svc.registry.apply(value,1)
        fields=self.manager.settings(value['services'][0]['id']);fields.pop('unit')
        fields['allow_control']=False
        checked=self.manager.check(fields);self.manager.save(checked['ticket'])
        self.assertEqual(self.svc.registry.read()['profiles'][0]['model_name'],'Verified model')
        self.assertFalse(self.svc.registry.read()['profiles'][0]['allow_control'])
