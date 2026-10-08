#!/usr/bin/python3
"""dpkg hook: refresh/remove only opted-in, running user managers."""
import os
import pwd
import subprocess
import sys
from pathlib import Path

action = sys.argv[1]
if action not in ('refresh', 'remove'):
    raise SystemExit(2)
failed = False
for entry in pwd.getpwall():
    if entry.pw_uid < 1000 or entry.pw_uid == 65534:
        continue
    runtime = Path('/run/user')/str(entry.pw_uid)
    marker = Path(entry.pw_dir)/'.local/share/dgx-spark-control/package-managed'
    if not (runtime/'bus').exists() or not marker.is_file():
        continue
    command = ['runuser', '-u', entry.pw_name, '--', 'env', 'XDG_RUNTIME_DIR='+str(runtime),
               'DBUS_SESSION_BUS_ADDRESS=unix:path='+str(runtime/'bus'),
               '/usr/bin/dgx-spark-control', action]
    try:
        result = subprocess.run(command, timeout=90, capture_output=True)
        success = result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        success = False
    if not success:
        failed = True
        print('DGX-SPARK-Control: user service action failed; run dgx-spark-control setup after login. / 로그인 후 초기 설정을 다시 실행하세요.', file=sys.stderr)
if failed:
    # Do not leave dpkg half-configured for a per-user runtime failure.
    print('Package files installed; dashboard runtime needs attention. / 패키지 설치 완료, 서버 확인 필요.', file=sys.stderr)
