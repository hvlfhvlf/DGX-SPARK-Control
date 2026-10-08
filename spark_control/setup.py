"""Local setup backend and CLI. No GTK import, no credentials in argv/output."""
import argparse
import getpass
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from .config import Config
from .desktop import connection, LOCAL_URL

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = Path('/usr/lib/dgx-spark-control')
VERSION = (ROOT/'VERSION').read_text().strip()
DATA_REL = '.local/share/dgx-spark-control'
UNITS = ('dgx-spark-control.service', 'dgx-spark-control-tray.service', 'dgx-spark-control.slice')


def run(args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=35, **kwargs)


def state(home=None):
    home = Path(home or Path.home())
    data = home/DATA_REL
    config = json.loads((data/'config.json').read_text()) if (data/'config.json').exists() else {}
    return {'version': VERSION, 'name': config.get('spark_name', 'DGX_SPARK'),
            'has_password': (data/'password.json').is_file(),
            'managed': (data/'package-managed').is_file(), 'language': config.get('setup_language', 'ko' if os.environ.get('LANG', '').startswith('ko') else 'en')}


def preflight():
    if os.geteuid() == 0:
        raise ValueError('Run setup as your desktop user, not root. / 일반 사용자로 설정을 실행하세요.')
    if platform.system() != 'Linux' or platform.machine() not in ('aarch64', 'arm64'):
        raise ValueError('This package supports Linux ARM64 DGX Spark only. / Linux ARM64 전용입니다.')
    if sys.version_info < (3, 12):
        raise ValueError('Python 3.12+ required / Python 3.12 이상이 필요합니다.')
    run(['systemctl', '--user', 'show-environment'])


def validate(name, password, confirm, existing):
    if not name.strip() or len(name.strip()) > 32 or any(ord(c) < 32 for c in name):
        raise ValueError('Name: 1–32 characters. / 이름은 1–32자로 입력하세요.')
    if password or confirm or not existing:
        if not 4 <= len(password) <= 128:
            raise ValueError('Password: 4–128 characters. / 비밀번호는 4–128자로 입력하세요.')
        if password != confirm:
            raise ValueError('Passwords do not match. / 비밀번호가 일치하지 않습니다.')


def health(data):
    token = (data/'access-token').read_text().strip()
    for _ in range(20):
        try:
            request = urllib.request.Request(LOCAL_URL+'/api/health', headers={'Authorization': 'Bearer '+token})
            with urllib.request.urlopen(request, timeout=2) as response:
                body = json.load(response)
            if body.get('status') == 'ok' and body.get('version') == VERSION:
                return
        except (OSError, ValueError):
            pass
        time.sleep(.5)
    raise RuntimeError('Dashboard health check failed. / 서버 상태 검사에 실패했습니다.')


def unit_files():
    base = '''[Unit]
Description=DGX-SPARK-Control dashboard
ConditionPathExists=/usr/lib/dgx-spark-control/spark_control/server.py
After=network.target
StartLimitIntervalSec=120
StartLimitBurst=3
[Service]
Type=simple
Slice=dgx-spark-control.slice
ExecStart=/usr/bin/dgx-spark-control server
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=PYTHONUNBUFFERED=1
Restart=on-failure
RestartSec=5
MemoryAccounting=yes
MemoryHigh=192M
MemoryMax=480M
MemorySwapMax=0
TasksMax=32
CPUWeight=10
UMask=0077
NoNewPrivileges=yes
RestrictSUIDSGID=yes
LockPersonality=yes
[Install]
WantedBy=default.target
'''
    tray = '''[Unit]
Description=DGX-SPARK-Control desktop tray
ConditionPathExists=/usr/lib/dgx-spark-control/spark_control/tray.py
PartOf=graphical-session.target
After=graphical-session.target
[Service]
Slice=dgx-spark-control.slice
ExecStart=/usr/bin/dgx-spark-control tray
Environment=PYTHONDONTWRITEBYTECODE=1
Restart=on-failure
RestartSec=10
MemoryMax=128M
MemorySwapMax=0
TasksMax=32
UMask=0077
NoNewPrivileges=yes
'''
    return {UNITS[0]: base, UNITS[1]: tray, UNITS[2]: '''[Unit]
Description=DGX-SPARK-Control total resource budget
[Slice]
MemoryAccounting=yes
CPUAccounting=yes
MemoryHigh=256M
MemoryMax=480M
MemorySwapMax=0
'''}


def activate(home=None):
    home = Path(home or Path.home())
    data = home/DATA_REL
    if not (data/'password.json').is_file():
        raise ValueError('Finish password setup first. / 비밀번호 설정을 먼저 완료하세요.')
    units = home/'.config/systemd/user'
    units.mkdir(parents=True, exist_ok=True)
    auto = home/'.config/autostart/dgx-spark-control-tray.desktop'
    auto.parent.mkdir(parents=True, exist_ok=True)
    backup = data/'backups'/('package-'+str(time.time_ns()))
    backup.mkdir(parents=True, mode=0o700)
    originals = {p: p.read_bytes() if p.exists() else None for p in [*(units/n for n in UNITS), auto]}
    for p, content in originals.items():
        if content is not None:
            (backup/p.name).write_bytes(content)
    # Private configuration remains outside dpkg-owned code. Do not change sessions.
    for name in ('config.json', 'password.json', 'sessions.json', 'access-token'):
        p = data/name
        if p.exists():
            shutil.copy2(p, backup/name)
            (backup/name).chmod(0o600)
    previously_running = subprocess.run(['systemctl', '--user', 'is-active', '--quiet', UNITS[0]]).returncode == 0
    try:
        for name, content in unit_files().items():
            (units/name).write_text(content)
        auto.write_text('[Desktop Entry]\nType=Application\nName=DGX-SPARK-Control\nTryExec=/usr/bin/dgx-spark-control\nExec=/usr/bin/dgx-spark-control start-tray\nTerminal=false\nX-GNOME-Autostart-enabled=true\n')
        run(['systemctl', '--user', 'daemon-reload'])
        run(['systemctl', '--user', 'enable', UNITS[0]])
        run(['systemctl', '--user', 'restart', UNITS[0]])
        health(data)
    except Exception:
        for p, content in originals.items():
            if content is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(content)
        run(['systemctl', '--user', 'daemon-reload'])
        subprocess.run(['systemctl', '--user', 'restart' if previously_running else 'stop', UNITS[0]], capture_output=True)
        if not previously_running and originals[units/UNITS[0]] is None:
            subprocess.run(['systemctl', '--user', 'disable', UNITS[0]], capture_output=True)
        raise
    (data/'package-managed').write_text(VERSION+'\n')
    (data/'package-managed').chmod(0o600)
    # Keep old command paths usable, but route their update/rollback guards to
    # package-owned code. Preserve the old release for migration recovery.
    app = home/'.local/share/dgx-spark-control-app'
    app.mkdir(parents=True, exist_ok=True)
    current = app/'current'
    if current.is_symlink() and current.resolve() != PACKAGE_ROOT:
        previous = app/'previous'
        previous.unlink(missing_ok=True)
        previous.symlink_to(os.readlink(current))
    if not current.exists() or current.is_symlink():
        temporary = app/'current.package-next'
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(PACKAGE_ROOT)
        os.replace(temporary, current)
    # Desktop availability is optional; browser/SSH-only installs still work.
    tray_started = False
    if subprocess.run(['systemctl', '--user', 'is-active', '--quiet', 'graphical-session.target']).returncode == 0:
        try:
            run(['systemctl', '--user', 'import-environment', 'DISPLAY', 'WAYLAND_DISPLAY', 'XAUTHORITY', 'XDG_CURRENT_DESKTOP'])
        except subprocess.SubprocessError:
            pass
        try:
            run(['systemctl', '--user', 'restart', UNITS[1]])
            tray_started = True
        except subprocess.SubprocessError:
            pass
    return {'ok': True, 'version': VERSION, 'local_url': LOCAL_URL, 'tailscale': connection(), 'tray_started': tray_started}


def configure(name, password='', confirm='', language='en'):
    preflight()
    existing = state()
    validate(name, password, confirm, existing['has_password'])
    data = Path.home()/DATA_REL
    if data.exists():
        backup = data/'backups'/('setup-'+str(time.time_ns()))
        backup.mkdir(parents=True, mode=0o700)
        for filename in ('config.json', 'password.json', 'sessions.json'):
            if (data/filename).is_file():
                shutil.copy2(data/filename, backup/filename)
                (backup/filename).chmod(0o600)
    config = Config(data)
    config.rename(name)
    if password:
        config.set_password(password)
    config.value['setup_language'] = language
    config.save()
    if not (config.directory/'hardware.json').exists():
        run([sys.executable, str(ROOT/'scripts/probe-hardware.py'), str(config.directory)])
    if ROOT == PACKAGE_ROOT:
        return activate()
    run(['bash', str(ROOT/'install.sh')])
    return {'ok': True, 'version': VERSION, 'local_url': LOCAL_URL, 'tailscale': connection()}


def main():
    parser = argparse.ArgumentParser(description='DGX Spark local setup / 로컬 초기 설정')
    parser.add_argument('--cli', action='store_true', help='Interactive terminal / 터미널 설정')
    parser.add_argument('--non-interactive', action='store_true', help='Preserve an existing password; never take a password in argv')
    parser.add_argument('--check', action='store_true', help='Read-only checks; JSON result / 읽기 전용 점검')
    parser.add_argument('--lang', choices=['ko', 'en'])
    args = parser.parse_args()
    preflight()
    current = state()
    if args.check:
        print(json.dumps({**current, 'tailscale': connection(), 'setup_required': not current['has_password']}, ensure_ascii=False))
    elif args.non_interactive:
        if not current['has_password']:
            print(json.dumps({'ok': False, 'setup_required': True, 'message': 'Run dgx-spark-control setup / 초기 설정을 실행하세요.'}))
            return 2
        if ROOT != PACKAGE_ROOT:
            raise ValueError('Use bash install.sh for archive updates / 압축 배포는 install.sh를 사용하세요.')
        print(json.dumps(activate(), ensure_ascii=False))
    elif args.cli:
        if not sys.stdin.isatty():
            raise ValueError('Interactive terminal required / 대화형 터미널이 필요합니다.')
        language = args.lang or ('ko' if input('Language / 언어 [ko/en]: ').strip().lower() == 'ko' else 'en')
        name = input(('Spark 표시 이름' if language == 'ko' else 'Spark display name')+' ['+current['name']+']: ').strip() or current['name']
        password = confirm = ''
        if not current['has_password']:
            password = getpass.getpass('비밀번호 / Password: ')
            confirm = getpass.getpass('확인 / Confirm: ')
        print(json.dumps(configure(name, password, confirm, language), ensure_ascii=False))
    else:
        from .wizard import main as show
        show(args.lang or current['language'])
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print('Setup failed / 설정 실패: '+str(exc), file=sys.stderr)
        sys.exit(1)
