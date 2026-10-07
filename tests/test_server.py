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
        for path in ['/api/metrics', '/api/settings', '/api/models', '/api/history', '/api/hardware']:
            with self.assertRaises(urllib.error.HTTPError) as error:
                self.request(path, token=False)
            self.assertEqual(error.exception.code, 401)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request('/api/settings', {'spark_name': 'Bad'}, origin='https://untrusted.example')
        self.assertEqual(error.exception.code, 403)

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
