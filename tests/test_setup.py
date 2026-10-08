import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from spark_control import setup
from spark_control.desktop import dashboard_url


class SetupTests(unittest.TestCase):
    def test_first_install_requires_confirmed_password(self):
        for password, confirm in [('', ''), ('abc', 'abc'), ('valid-password', 'different')]:
            with self.assertRaises(ValueError):
                setup.validate('Spark', password, confirm, False)
        setup.validate('나의 Spark', 'valid-password', 'valid-password', False)
        setup.validate('Spark', '', '', True)
        for name in ('', 'x'*33, 'line\nbreak'):
            with self.assertRaises(ValueError):
                setup.validate(name, '', '', True)

    def test_readonly_state_does_not_create_files(self):
        with tempfile.TemporaryDirectory() as directory:
            before = list(Path(directory).rglob('*'))
            self.assertFalse(setup.state(directory)['has_password'])
            self.assertEqual(before, list(Path(directory).rglob('*')))

    def test_activation_rejects_missing_password_before_any_service_action(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(setup, 'run') as run:
            with self.assertRaises(ValueError):
                setup.activate(directory)
            run.assert_not_called()

    def test_failed_migration_restores_units_and_does_not_mark_managed(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            data = home/setup.DATA_REL
            data.mkdir(parents=True)
            (data/'password.json').write_text('{"test":true}')
            units = home/'.config/systemd/user'
            units.mkdir(parents=True)
            (units/setup.UNITS[0]).write_text('original unit')
            with patch.object(setup, 'run'), patch.object(setup.subprocess, 'run', return_value=Mock(returncode=0)), patch.object(setup, 'health', side_effect=RuntimeError('test failed')):
                with self.assertRaises(RuntimeError):
                    setup.activate(home)
            self.assertEqual((units/setup.UNITS[0]).read_text(), 'original unit')
            self.assertFalse((data/'package-managed').exists())
            self.assertFalse((units/setup.UNITS[1]).exists())
            self.assertEqual((data/'password.json').read_text(), '{"test":true}')

    def test_tailscale_only_uses_dashboard_route_not_other_apps_or_funnel(self):
        host = 'example.tail0000.ts.net:443'
        config = {'Web': {host: {'Handlers': {'/': {'Proxy': 'http://127.0.0.1:8767'}}}}}
        self.assertEqual(dashboard_url(config), 'https://example.tail0000.ts.net')
        config['AllowFunnel'] = {host: True}
        self.assertIsNone(dashboard_url(config))
        config.pop('AllowFunnel')
        config['Web'][host]['Handlers']['/']['Proxy'] = 'http://127.0.0.1:8888'
        self.assertIsNone(dashboard_url(config))

    def test_translation_keys_match(self):
        # Parse the literal without requiring GTK on headless hosts.
        import ast
        tree = ast.parse((setup.ROOT/'spark_control/wizard.py').read_text())
        translations = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TEXT' for t in n.targets))
        self.assertEqual(set(translations['ko']), set(translations['en']))
