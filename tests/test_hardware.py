import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from spark_control.hardware import identity, parse_installed_memory


class HardwareTests(unittest.TestCase):
    def test_different_capacities_and_empty_slots(self):
        for gb in [64, 128, 256]:
            self.assertEqual(parse_installed_memory(f'Memory Device\n Size: {gb} GB\n Size: No Module Installed\n'), gb * 2**30)
        self.assertEqual(parse_installed_memory(' Size: 32768 MB\n Size: 32768 MB\n'), 64 * 2**30)
        self.assertIsNone(parse_installed_memory(' Size: 64 GB\n Size: Unknown\n'))
        self.assertIsNone(parse_installed_memory(' Size: No Module Installed\n'))

    def test_missing_firmware_uses_explicit_os_capacity(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('spark_control.metrics.read', side_effect=lambda path: 'MemTotal: 62500000 kB\n' if path == '/proc/meminfo' else ''):
                result = identity(directory, None)
                self.assertIsNone(result['installed_memory_bytes'])
                self.assertIsNone(result['gpu_name'])
                self.assertEqual(result['os_memory_bytes'], 62500000 * 1024)
                self.assertEqual(result['memory_kind'], 'system')
                (Path(directory)/'hardware.json').write_text(json.dumps({'installed_memory_bytes': 64*2**30}))
                self.assertEqual(identity(directory, 'NVIDIA GB10')['installed_memory_bytes'], 64*2**30)
