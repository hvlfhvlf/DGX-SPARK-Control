#!/usr/bin/python3
"""Fixed-action user client. login1/polkit authorizes only reboot and poweroff."""
import json
import os
import subprocess
import sys


def query(method):
    r=subprocess.run(['/usr/bin/busctl','--json=short','call','org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager',method],capture_output=True,text=True,timeout=3,check=True)
    return json.loads(r.stdout)['data'][0]


def check():
    inhibitors=query('ListInhibitors')
    if any('shutdown' in row[0].split(':') and row[3]=='block' for row in inhibitors): return False
    uid=os.getuid()
    if uid<1000: return False
    if any(int(row[1])>=1000 and int(row[1])!=uid for row in query('ListSessions')): return False
    return True


def main():
    if os.getuid()<1000 or len(sys.argv)!=2 or sys.argv[1] not in ('check','reboot','poweroff','execute-reboot','execute-poweroff'): return 1
    try:
        allowed=check() and query('CanReboot')=='yes' and query('CanPowerOff')=='yes'
        if sys.argv[1]=='check': print(json.dumps(dict(enabled=allowed,reason=None if allowed else 'inhibitor_or_other_session')));return 0
        if not allowed: return 1
        action=sys.argv[1].removeprefix('execute-')
        method='Reboot' if action=='reboot' else 'PowerOff'
        if sys.argv[1].startswith('execute-'):
            subprocess.run(['/usr/bin/busctl','call','org.freedesktop.login1','/org/freedesktop/login1','org.freedesktop.login1.Manager',method,'b','false'],check=True,timeout=3,capture_output=True)
            return 0
        # User timer preserves server hardening and rechecks blockers at execution.
        subprocess.run(['/usr/bin/systemd-run','--user','--quiet','--collect','--unit=dgx-spark-control-power','--on-active=3s',
            '--property=Slice=dgx-spark-control.slice','--property=NoNewPrivileges=yes',
            '/usr/bin/python3','/usr/lib/dgx-spark-control/packaging/power-helper.py','execute-'+action],check=True,timeout=3,capture_output=True)
        print(json.dumps(dict(accepted=True)));return 0
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError): return 1


if __name__=='__main__': sys.exit(main())
