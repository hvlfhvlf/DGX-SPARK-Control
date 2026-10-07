import tempfile
import unittest
import time
from unittest.mock import patch
from pathlib import Path
from spark_control.config import Config
from spark_control.sessions import Sessions


class SessionTests(unittest.TestCase):
    def test_survives_restart_and_resets_with_password(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(directory)
            config.set_password('old-test-fixture')
            session = Sessions(config).issue()
            self.assertTrue(Sessions(Config(directory)).valid(session))
            with patch('spark_control.sessions.time.time', return_value=time.time()+365*86400):
                self.assertTrue(Sessions(Config(directory)).valid(session))
            self.assertNotIn(session, (Path(directory)/'sessions.json').read_text())
            config.set_password('new-test-fixture')
            self.assertFalse(Sessions(Config(directory)).valid(session))

    def test_sessions_bounded_and_logout_persists(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(directory)
            store = Sessions(config)
            oldest = store.issue()
            for _ in range(32):
                newest = store.issue()
            self.assertFalse(store.valid(oldest))
            self.assertEqual(len(store.values), 32)
            store.revoke(newest)
            self.assertFalse(Sessions(config).valid(newest))
