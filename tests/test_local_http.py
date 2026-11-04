import unittest
from unittest.mock import patch,MagicMock
from spark_control.local_http import connection


class LocalHTTPTests(unittest.TestCase):
    def test_loopback_first_and_no_redirect(self):
        with patch('spark_control.local_http.http.client.HTTPConnection') as http,patch('spark_control.local_http.bound_address') as address:
            self.assertIs(connection(18888),http.return_value)
            address.assert_not_called()
            http.assert_called_once_with('127.0.0.1',18888,timeout=1)
    def test_only_verified_local_bound_address_after_refused(self):
        first,second=MagicMock(),MagicMock();first.connect.side_effect=ConnectionRefusedError()
        with patch('spark_control.local_http.http.client.HTTPConnection',side_effect=[first,second]) as http,patch('spark_control.local_http.bound_address',return_value='100.64.0.2'):
            self.assertIs(connection(18888),second)
            self.assertEqual(http.call_args.args,('100.64.0.2',18888))
        with patch('spark_control.local_http.http.client.HTTPConnection',return_value=first),patch('spark_control.local_http.bound_address',return_value=None):
            with self.assertRaises(ConnectionRefusedError):connection(18888)
