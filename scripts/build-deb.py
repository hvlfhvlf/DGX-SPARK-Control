"""Build ARM64 Ubuntu package; root is not needed. Run on Linux with dpkg-deb."""
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
version = (root/'VERSION').read_text().strip()
output = root/'dist'
output.mkdir(exist_ok=True)
name = f'dgx-spark-control_{version}_arm64.deb'
with tempfile.TemporaryDirectory(prefix='dgx-deb-') as tmp:
    package = Path(tmp)
    lib = package/'usr/lib/dgx-spark-control'
    lib.mkdir(parents=True)
    for item in ('spark_control', 'web', 'scripts', 'docs', 'packaging'):
        shutil.copytree(root/item, lib/item, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for item in ('VERSION', 'README.md', 'CHANGELOG.md', 'AGENTS.md', 'install.sh', 'update.sh'):
        shutil.copy2(root/item, lib/item)
    binary = package/'usr/bin/dgx-spark-control'
    binary.parent.mkdir(parents=True)
    shutil.copy2(root/'packaging/dgx-spark-control', binary)
    binary.chmod(0o755)
    desktop = package/'usr/share/applications/dgx-spark-control.desktop'
    desktop.parent.mkdir(parents=True)
    desktop.write_text('[Desktop Entry]\nType=Application\nName=DGX-SPARK-Control Setup\nName[ko]=DGX-SPARK-Control 초기 설정\nComment=Set up your Spark dashboard\nComment[ko]=Spark 대시보드 설치 마무리 및 연결 확인\nExec=dgx-spark-control setup\nIcon=dgx-spark-control\nTerminal=false\nCategories=System;Monitor;\n')
    icon = package/'usr/share/icons/hicolor/scalable/apps/dgx-spark-control.svg'
    icon.parent.mkdir(parents=True)
    shutil.copy2(root/'web/icon.svg', icon)
    meta = package/'DEBIAN'
    meta.mkdir()
    meta.joinpath('control').write_text(f'''Package: dgx-spark-control
Version: {version}
Architecture: arm64
Maintainer: DGX-SPARK-Control contributors <noreply@github.com>
Section: utils
Priority: optional
Depends: python3 (>= 3.12), python3-gi, gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, dbus-user-session, systemd, xdg-utils
Recommends: gnome-shell-extension-appindicator
Installed-Size: {sum(p.stat().st_size for p in lib.rglob('*') if p.is_file())//1024+64}
Homepage: https://github.com/hvlfhvlf/DGX-SPARK-Control
Description: Lightweight DGX Spark dashboard and bilingual setup
 Local web telemetry, desktop tray and Korean/English first-run setup.
 Uses a bounded user service; does not install or alter model engines.
''')
    for hook, text in {
        'postinst': 'if [ "$1" = configure ]; then\n /usr/bin/python3 /usr/lib/dgx-spark-control/packaging/session-maintenance.py refresh\nfi\necho "Open DGX-SPARK-Control Setup from Applications. / 앱 메뉴에서 초기 설정을 실행하세요."',
        'prerm': 'case "$1" in remove|deconfigure) /usr/bin/python3 /usr/lib/dgx-spark-control/packaging/session-maintenance.py remove ;; esac',
    }.items():
        p = meta/hook
        p.write_text('#!/bin/sh\nset -e\n'+text+'\nexit 0\n')
        p.chmod(0o755)
    for p in package.rglob('*'):
        if p.is_dir():
            p.chmod(0o755)
        elif p not in (binary, meta/'postinst', meta/'prerm'):
            p.chmod(0o644)
    subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(package), str(output/name)], check=True)
checksum = hashlib.sha256((output/name).read_bytes()).hexdigest()
sums = output/'SHA256SUMS'
existing = sums.read_text().splitlines() if sums.exists() else []
sums.write_text('\n'.join([line for line in existing if not line.endswith('  '+name)]+[checksum+'  '+name])+'\n')
print(name, checksum)
