import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from spark_control.app_launch import harness_url
from spark_control.services import Services, ServiceError
from types import SimpleNamespace


class AppLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.log = self.home / '.local/share/deepseek-harness/logs/web.log'
        self.log.parent.mkdir(parents=True)
        self.url = 'https://example.test:9443/?token=' + 'a' * 32
        self.log.write_text(self.url)
        self.profile = dict(manager={'unit': 'deepseek-harness.service', 'type': 'systemd-user'}, allow_control=True, open_url='https://example.test:9443/')
        self.response = MagicMock(status=303)
        self.response.getheader.side_effect = lambda k: {'Set-Cookie': 'session=fixture', 'Location': './'}.get(k)
        self.conn = MagicMock()
        self.conn.getresponse.return_value = self.response
        self.patches = [patch('spark_control.app_launch.Path.home', return_value=self.home), patch('spark_control.app_launch.http.client.HTTPConnection', return_value=self.conn)]
        for p in self.patches: p.start()

    def tearDown(self):
        for p in self.patches: p.stop()
        self.temp.cleanup()

    def test_latest_token_and_bounded_source_without_persistence(self):
        self.assertEqual(harness_url(self.profile)['url'], self.url)
        self.log.write_text('x' * 70000 + '\n' + self.url + '\n' + self.url.replace('a'*32, 'b'*32))
        self.assertIn('b'*32, harness_url(self.profile)['url'])
        self.conn.close.assert_called()

    def test_wrong_destination_unknown_unit_and_disabled_control_rejected(self):
        for change in ({'open_url': 'https://other.test/'}, {'allow_control': False}, {'manager': {'unit': 'other.service'}}):
            with self.assertRaisesRegex(ValueError, '^app_launch_unavailable$'):
                harness_url({**self.profile, **change})

    def test_bad_token_extra_parameters_and_redirect_rejected(self):
        for url in (self.url + '&next=https://other.test', self.url + '#secret', self.url.replace('a'*32, 'short')):
            self.log.write_text(url)
            with self.assertRaisesRegex(ValueError, '^app_launch_unavailable$'): harness_url(self.profile)
        self.log.write_text(self.url)
        self.response.status = 401
        with self.assertRaisesRegex(ValueError, '^app_launch_unavailable$'): harness_url(self.profile)
        self.response.status = 303
        self.response.getheader.side_effect = lambda k: 'https://other.test/' if k == 'Location' else 'cookie'
        with self.assertRaisesRegex(ValueError, '^app_launch_unavailable$'): harness_url(self.profile)

    def test_launch_checks_revision_unit_and_state(self):
        svc = Services(SimpleNamespace(directory=self.home/'dashboard', value={'models': []}))
        profile = dict(self.profile, id='harness-default', service_id='harness', name='Default')
        svc.registry.apply(dict(registry_schema=1, revision=0, services=[dict(id='harness', name='Harness', adapter='process', default_profile_id='harness-default')], profiles=[profile], assets=[]), 0)
        with self.assertRaisesRegex(ServiceError, 'revision_conflict'): svc.open_app({'id':'harness','revision':0})
        with patch('spark_control.services.system_states', return_value={'deepseek-harness.service': {'ActiveState':'inactive'}}):
            with self.assertRaisesRegex(ServiceError, 'app_launch_unavailable'): svc.open_app({'id':'harness','revision':1})
        with patch('spark_control.services.system_states', return_value={'deepseek-harness.service': {'LoadState':'loaded', 'ActiveState':'active'}}):
            self.assertEqual(svc.open_app({'id':'harness','revision':1})['url'], self.url)
