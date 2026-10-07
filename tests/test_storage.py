import unittest
from types import SimpleNamespace
from unittest.mock import patch
from spark_control.metrics import filesystem_usage


class StorageTests(unittest.TestCase):
    def test_reserved_space_is_not_reported_as_used(self):
        volume = SimpleNamespace(f_blocks=1000, f_bfree=400, f_bavail=350, f_frsize=4096)
        with patch('spark_control.metrics.os.statvfs', return_value=volume):
            sample = filesystem_usage('/')
        self.assertEqual(sample['disk_used_bytes'], 600*4096)
        self.assertEqual(sample['disk_available_bytes'], 350*4096)
        self.assertEqual(sample['disk_reserved_free_bytes'], 50*4096)
        self.assertEqual(sample['disk_used_percent'], 60)
        self.assertEqual(sample['disk_df_percent'], 64)
        self.assertEqual(sample['disk_mount'], '/')
