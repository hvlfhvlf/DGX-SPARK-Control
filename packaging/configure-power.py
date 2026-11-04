#!/usr/bin/python3
"""Explicit local administrator opt-in. Never executes a power action."""
import argparse
import os
import pwd
import re
import tempfile
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--user',required=True);p.add_argument('--disable',action='store_true');a=p.parse_args()
if os.geteuid()!=0 or not re.fullmatch(r'[a-z_][a-z0-9_-]*',a.user) or pwd.getpwnam(a.user).pw_uid<1000:
    raise SystemExit('A local administrator and normal user are required')
target=Path('/etc/polkit-1/rules.d/49-dgx-spark-control-power-'+a.user+'.rules')
legacy=Path('/etc/sudoers.d/dgx-spark-control-power-'+a.user)
if a.disable:
    target.unlink(missing_ok=True);legacy.unlink(missing_ok=True);print('Power control opt-in removed');raise SystemExit()
helper=Path('/usr/lib/dgx-spark-control/packaging/power-helper.py')
if helper.stat().st_uid!=0 or helper.stat().st_mode & 0o022:
    raise SystemExit('Helper must be root-owned and not group/world writable')
text='''// Explicit account opt-in; no multiple-session or ignore-inhibitor grants.
polkit.addRule(function(action, subject) {
    if (subject.user === "'''+a.user+'''" &&
        (action.id === "org.freedesktop.login1.reboot" ||
         action.id === "org.freedesktop.login1.power-off")) {
        return polkit.Result.YES;
    }
});
'''
with tempfile.NamedTemporaryFile(mode='w',dir=target.parent,prefix='.dgx-power-',delete=False) as f:
    temp=Path(f.name);f.write(text)
try:
    temp.chmod(0o644);os.replace(temp,target);legacy.unlink(missing_ok=True)
    print('Power control enabled; server hardening unchanged')
finally: temp.unlink(missing_ok=True)
