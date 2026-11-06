import socket
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from spark_control.services import Services, ServiceError
from test_services import fixture, states


class PortRecoveryTests(unittest.TestCase):
    def test_time_wait_allows_start_but_live_listener_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp, socket.socket() as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(('127.0.0.1', 0));listener.listen()
            port=listener.getsockname()[1]
            svc=Services(SimpleNamespace(directory=Path(tmp),value={'models':[]}))
            data=fixture();data['profiles'][0]['probe']={'origin':f'http://127.0.0.1:{port}'}
            svc.registry.apply(data,0)
            with patch('spark_control.services.system_states',side_effect=states):
                with self.assertRaisesRegex(ServiceError,'probe_port_in_use'):
                    svc.action('test','start')
                with socket.create_connection(('127.0.0.1',port)) as client:
                    accepted,_=listener.accept();accepted.close()
                    self.assertEqual(client.recv(1),b'')
                listener.close()
                # Server side closed first, leaving TIME_WAIT on the service port.
                done=threading.Event()
                def completed(guard,op,service,profile):
                    guard.__exit__(None,None,None);done.set()
                with patch.object(svc,'_execute',side_effect=completed):
                    result=svc.action('test','start')
                    self.assertEqual(result['status'],'queued');self.assertTrue(done.wait(2))
