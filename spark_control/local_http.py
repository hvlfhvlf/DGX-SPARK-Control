"""HTTP to this host only, including engines bound to its Tailscale interface."""
import http.client
import ipaddress
import json
from pathlib import Path
import socket
import subprocess
import threading
import time

_lock=threading.Lock()
_at=0
_addresses=set()


def bound_address(port):
    global _at,_addresses
    with _lock:
        if time.monotonic()-_at>30:
            _addresses=set()
            try:
                result=subprocess.run(['ip','-j','-4','address','show'],capture_output=True,timeout=1)
                if result.returncode==0 and len(result.stdout)<=131072:
                    for interface in json.loads(result.stdout):
                        for info in interface.get('addr_info',[]):
                            address=info.get('local','')
                            if isinstance(ipaddress.ip_address(address),ipaddress.IPv4Address):
                                _addresses.add(address)
            except (OSError,ValueError,subprocess.TimeoutExpired):
                pass
            _at=time.monotonic()
        try:
            for line in Path('/proc/net/tcp').read_text().splitlines()[1:4097]:
                fields=line.split()
                if fields[3]!='0A':continue
                address,hexport=fields[1].split(':')
                if int(hexport,16)!=port:continue
                address=socket.inet_ntoa(bytes.fromhex(address)[::-1])
                if address in _addresses and not ipaddress.ip_address(address).is_loopback:
                    return address
        except (OSError,ValueError,IndexError):
            pass
    return None


def connection(port, timeout=1):
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=timeout)
    try:
        conn.connect()
        return conn
    except ConnectionRefusedError:
        conn.close()
        address=bound_address(port)
        if address is None:raise
        conn=http.client.HTTPConnection(address,port,timeout=timeout)
        try:
            conn.connect()
        except Exception:
            conn.close()
            raise
        return conn
    except Exception:
        conn.close()
        raise
