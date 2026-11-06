import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from spark_control.config import Config
from spark_control.server import Server


class ServerTests(unittest.TestCase):
    def test_incremental_history_reset_cursor_and_auth(self):
        now = time.time()
        self.server.collector.history.extend([{'timestamp': now - 5, 'cpu': 1}, {'timestamp': now, 'cpu': 2}])
        first = self.request('/api/history?incremental=1')
        self.assertTrue(first['reset'])
        self.assertEqual(len(first['samples']), 2)
        base = '/api/history?incremental=1&epoch=' + first['epoch'] + '&since='
        self.assertEqual(self.request(base + str(now))['samples'], [])
        self.assertEqual(len(self.request(base + str(now - 5))['samples']), 1)
        self.assertTrue(self.request(base + str(now + 60))['reset'])
        self.assertTrue(self.request('/api/history?incremental=1&epoch=old&since=' + str(now))['reset'])
        for bad in ('nan', 'inf', '-1', 'invalid'):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request(base + bad)
            self.assertEqual(error.exception.code, 400)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/history?incremental=1', token=False)
        self.assertEqual(error.exception.code, 401)
        self.assertIsInstance(self.request('/api/history'), list)

    def test_saturation_returns_retryable_503_without_new_workers(self):
        for _ in range(8):
            self.server.slots.acquire()
        try:
            started = time.monotonic()
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request('/api/info', token=False)
            self.assertEqual(error.exception.code, 503)
            self.assertEqual(error.exception.headers['Retry-After'], '1')
            self.assertLess(time.monotonic() - started, 2)
        finally:
            for _ in range(8):
                self.server.slots.release()
        self.assertEqual(self.request('/api/info', token=False)['mode'], 'live')

    def test_short_burst_waits_for_a_worker(self):
        for _ in range(8):
            self.server.slots.acquire()
        timer = threading.Timer(0.05, self.server.slots.release)
        timer.start()
        try:
            self.assertEqual(self.request('/api/info', token=False)['mode'], 'live')
        finally:
            timer.join()
            for _ in range(7):
                self.server.slots.release()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = Config(self.temp.name)
        self.server = Server(('127.0.0.1', 0), self.config)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, body=None, token=True, origin=None):
        headers = {'Authorization': 'Bearer ' + self.config.token} if token else {}
        if origin:
            headers['Origin'] = origin
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode() if body is not None else None, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.load(response)

    def test_auth_and_origin(self):
        self.assertEqual(self.request('/api/info', token=False)['mode'], 'live')
        for path in ['/api/services/update?id=example','/api/inference','/api/connections/settings','/api/models/roots','/api/metrics', '/api/settings', '/api/models', '/api/history', '/api/hardware', '/api/services', '/api/programs', '/api/power/status', '/api/events']:
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request(path, token=False)
            self.assertEqual(error.exception.code, 401)
        for path in ['/api/services/update/check','/api/services/update/apply','/api/services/open','/api/models/register','/api/connections/discover','/api/connections/check','/api/connections/save','/api/models/roots','/api/services/action', '/api/services/discover', '/api/services/register', '/api/services/display', '/api/services/order', '/api/power/prepare', '/api/power/confirm', '/api/events/clear']:
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request(path, {}, token=False)
            self.assertEqual(error.exception.code, 401)
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request(path, {}, origin='https://untrusted.example')
            self.assertEqual(error.exception.code, 403)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/settings', {'spark_name': 'Bad'}, origin='https://untrusted.example')
        self.assertEqual(error.exception.code, 403)

    def test_autostart_auth_origin_and_routing(self):
        for body in (None, {}):
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request('/api/services/autostart?id=example', body, token=False)
            self.assertEqual(error.exception.code, 401)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/services/autostart', {}, origin='https://untrusted.example')
        self.assertEqual(error.exception.code, 403)
        with patch.object(self.server.autostart, 'status', return_value={'enabled':False}) as status, patch.object(self.server.autostart, 'set', return_value={'enabled':True}) as change:
            self.assertFalse(self.request('/api/services/autostart?id=example')['enabled'])
            status.assert_called_once_with('example');change.assert_not_called()
            self.assertTrue(self.request('/api/services/autostart', {'id':'example','enabled':True})['enabled'])
            change.assert_called_once()

    def test_power_wrong_password_does_not_log_out_and_get_never_mutates(self):
        self.config.set_password('test-fixture-only')
        with patch('spark_control.power.helper',side_effect=lambda action: {'enabled':True} if action=='check' else {'accepted':True}) as helper:
            self.assertTrue(self.request('/api/power/status')['enabled'])
            with self.assertRaises(urllib.error.HTTPError):self.request('/api/power/confirm')
            prepared=self.request('/api/power/prepare',{'action':'reboot'})
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request('/api/power/confirm',dict(action='reboot',confirmation=prepared['confirmation'],password='wrong'))
            self.assertEqual(error.exception.code,409)
            self.assertEqual(self.request('/api/health')['status'],'ok')
            self.assertTrue(all(call.args[0]=='check' for call in helper.call_args_list))

    def test_activity_clear_http_does_not_erase_service_operations(self):
        self.server.services.operations=[dict(id='fixture',service_id='test',action='stop',status='completed',created_at=1,finished_at=2)]
        self.assertEqual(len(self.request('/api/events')),1)
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/events/clear')
        self.assertEqual(self.request('/api/events/clear',{'through':2})['cleared'],1)
        self.assertEqual(self.request('/api/events'),[])
        self.assertEqual(len(self.server.services.operations),1)

    def test_service_display_and_order_http_persistence(self):
        from spark_control.services import Registry
        value = dict(registry_schema=1, revision=0, services=[dict(id='test', name='Test', adapter='process', default_profile_id='one')],
            profiles=[dict(id='one', service_id='test', name='One', manager=dict(type='systemd-user', unit='fixture.service'))], assets=[])
        self.server.services.registry.apply(value, 0)
        with patch('spark_control.services.subprocess.run') as run:
            result = self.request('/api/services/display', dict(id='test', profile_id='one', revision=1, fields={'name':'My service', 'model_name':'Model name'}))
            self.assertEqual(result['revision'], 2)
            self.request('/api/services/order', dict(ids=['test'], revision=2))
            restored = Registry(self.temp.name).read()
            self.assertEqual(restored['revision'], 3)
            self.assertEqual(restored['services'][0]['name'], 'My service')
            self.assertEqual(restored['profiles'][0]['model_name'], 'Model name')
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request('/api/services/display', dict(id='test', profile_id='one', revision=1, fields={'name':'Stale'}))
            self.assertEqual(error.exception.code, 409)
            self.assertEqual(Registry(self.temp.name).read(), restored)
            run.assert_not_called()

    def test_name_survives_restart_and_invalid_names(self):
        self.assertEqual(self.request('/api/settings')['spark_name'], 'DGX_SPARK')
        self.request('/api/settings', {'spark_name': '  나의 Spark  '})
        self.assertEqual(Config(self.temp.name).value['spark_name'], '나의 Spark')
        for value in ['', '   ', 'x' * 33, 3, '\nName']:
            with self.assertRaises(urllib.error.HTTPError):
                self.request('/api/settings', {'spark_name': value})

    def test_controls_allowlist(self):
        with patch('spark_control.models.subprocess.run') as run:
            for payload in [{'id': 'unknown', 'action': 'start'}, {'id': 'unknown', 'action': 'rm -rf /'}]:
                with self.assertRaises(urllib.error.HTTPError):
                    self.request('/api/models/action', payload)
            run.assert_not_called()

    def test_path_traversal_and_unknown_api(self):
        for path in ['/../VERSION', '/%2e%2e/config.json', '/api/not-real']:
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request(path)
            self.assertEqual(error.exception.code, 404)

    def test_collector_cache_and_missing_first_rates(self):
        first = self.request('/api/metrics')
        self.assertIsNone(first['cpu'])
        self.assertEqual(first['network'], [None, None])
        second = self.request('/api/metrics')
        self.assertEqual(first['timestamp'], second['timestamp'])
        self.assertEqual(self.request('/api/health')['collections'], 1)
        self.assertEqual(len(self.request('/api/history')), 1)
        self.assertGreater(first['memory_total_gib'], 0)

    def test_password_sessions_logout_and_expiry(self):
        self.config.set_password('test-fixture-only')
        self.assertEqual(self.request('/api/info', token=False)['auth_mode'], 'password')
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/login', {'password': 'wrong-fixture'}, token=False)
        self.assertEqual(error.exception.code, 401)
        login = self.request('/api/login', {'password': 'test-fixture-only'}, token=False)
        session = login['session']
        self.assertNotEqual(session, self.config.token)
        self.assertIsNone(login['expires_in'])

        def session_request(path, body=None):
            req = urllib.request.Request(self.url+path, data=json.dumps(body).encode() if body is not None else None, headers={'Authorization': 'Bearer '+session})
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.load(response)
        self.assertEqual(session_request('/api/health')['status'], 'ok')
        with patch('spark_control.sessions.time.time', return_value=time.time()+28801):
            self.assertEqual(session_request('/api/health')['status'], 'ok')
        session = self.request('/api/login', {'password': 'test-fixture-only'}, token=False)['session']
        self.assertTrue(session_request('/api/logout', {})['ok'])
        with self.assertRaises(urllib.error.HTTPError):
            session_request('/api/health')
        self.assertTrue(Config(self.temp.name).check_password('test-fixture-only'))
        self.assertNotIn('test-fixture-only', (Path(self.temp.name)/'password.json').read_text())


if __name__ == '__main__':
    unittest.main()
