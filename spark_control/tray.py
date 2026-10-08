"""Optional local desktop controls. No telemetry polling or model workload ownership."""
import json
import subprocess
import uuid
import urllib.error
import urllib.request
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as Indicator
except ValueError:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as Indicator

from .config import Config
from .desktop import connection, open_url, launch, RELEASES, LOCAL_URL

ROOT = Path(__file__).resolve().parent.parent
DATA = Path.home()/'.local/share/dgx-spark-control'
SERVICE = 'dgx-spark-control.service'


def service(action):
    subprocess.run(['systemctl', '--user', action, SERVICE], check=True, timeout=15, capture_output=True)


def rename(name):
    config = Config(DATA)
    request = urllib.request.Request('http://127.0.0.1:8767/api/settings', data=json.dumps({'spark_name': name}).encode(), headers={'Authorization': 'Bearer '+config.token})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            json.load(response)
    except urllib.error.HTTPError:
        raise ValueError('Could not save the name. Use 1-32 characters.')
    except urllib.error.URLError:
        # When the server is stopped, save for its next start.
        config.rename(name)


class Tray:
    def __init__(self):
        self.indicator = Indicator.Indicator.new('dgx-spark-control', str(ROOT/'web/icon.svg'), Indicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_title('DGX-SPARK-Control')
        self.indicator.set_status(Indicator.IndicatorStatus.ACTIVE)
        self.menu = Gtk.Menu()
        self.add('DGX-SPARK-Control · '+(ROOT/'VERSION').read_text().strip(), None)
        self.add('Open dashboard / 대시보드 열기', self.open_dashboard)
        self.add('Copy connection address / 접속 주소 복사', self.copy_address)
        self.add('Setup / 초기 설정', self.open_setup)
        self.add('Check for updates / 업데이트 확인', lambda *_: open_url(RELEASES))
        self.add('Change Spark name / 이름 변경', lambda *_: self.edit(False))
        self.add('Reset password / 비밀번호 재설정', lambda *_: self.edit(True))
        self.menu.append(Gtk.SeparatorMenuItem())
        self.add('Start dashboard / 서버 시작', lambda *_: self.server_action('start'))
        self.add('Restart dashboard / 서버 재시작', lambda *_: self.server_action('restart'))
        self.add('Status / 상태', self.status)
        self.menu.append(Gtk.SeparatorMenuItem())
        self.add('Close tray / 트레이 닫기', lambda *_: Gtk.main_quit())
        self.menu.show_all()
        self.indicator.set_menu(self.menu)

    def add(self, label, callback):
        item = Gtk.MenuItem(label=label)
        if callback:
            item.connect('activate', callback)
        else:
            item.set_sensitive(False)
        self.menu.append(item)

    def message(self, text):
        dialog = Gtk.MessageDialog(message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text=text)
        dialog.set_title('DGX-SPARK-Control')
        dialog.set_keep_above(True)
        dialog.run()
        dialog.destroy()

    def open_dashboard(self, *_):
        # A desktop browser is separate from the bounded monitoring/tray service.
        subprocess.Popen(['systemd-run', '--user', '--collect', '--unit=dgx-dashboard-browser-'+uuid.uuid4().hex[:8], '/usr/bin/xdg-open', 'http://127.0.0.1:8767'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def copy_address(self, *_):
        result = connection()
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(result['url'] or LOCAL_URL, -1)
        clipboard.store()
        self.message(('Tailscale address copied / Tailscale 주소 복사 완료' if result['url'] else 'Local address copied. Set up Tailscale for other devices. / 로컬 주소를 복사했습니다. 다른 기기에서는 Tailscale 설정이 필요합니다.'))

    def open_setup(self, *_):
        if (DATA/'package-managed').exists():
            launch(['/usr/bin/dgx-spark-control', 'setup'])
        else:
            launch(['/usr/bin/python3', str(ROOT/'scripts/open-setup.py')])

    def server_action(self, action):
        try:
            service(action)
            self.message('Dashboard '+action+' complete.\n모델 서비스는 변경하지 않았습니다.')
        except (OSError, subprocess.SubprocessError):
            self.message('Dashboard service operation failed. Check its local journal.')

    def status(self, *_):
        result = subprocess.run(['systemctl', '--user', 'is-active', SERVICE], capture_output=True, text=True, timeout=3)
        self.message('DGX-SPARK-Control\n'+Config(DATA).value['spark_name']+'\nServer / 서버: '+result.stdout.strip()+'\n'+LOCAL_URL+'\n'+(connection()['url'] or 'Tailscale: setup required / 연결 설정 필요')+'\n\nLocal desktop control. No telemetry polling in the tray.\n로컬 데스크톱 제어. 트레이는 지표를 주기적으로 수집하지 않습니다.')

    def edit(self, password):
        dialog = Gtk.Dialog(title='Reset password / 비밀번호 재설정' if password else 'Spark name / Spark 이름')
        dialog.set_keep_above(True)
        dialog.set_default_size(390, 180)
        dialog.add_buttons('Cancel / 취소', Gtk.ResponseType.CANCEL, 'Save / 저장', Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_border_width(18)
        box.set_spacing(12)
        note = Gtk.Label(label='로컬 Spark 사용자 권한으로 재설정합니다.\n기존 비밀번호는 필요하지 않으며 웹 로그인은 해제됩니다.' if password else '웹 대시보드의 표시 이름을 변경합니다.')
        box.pack_start(note, False, False, 0)
        first = Gtk.Entry()
        first.set_max_length(128 if password else 32)
        first.set_visibility(not password)
        first.set_placeholder_text('New password / 새 비밀번호' if password else 'Spark name')
        if not password:
            first.set_text(Config(DATA).value['spark_name'])
        box.pack_start(first, False, False, 0)
        second = Gtk.Entry()
        if password:
            second.set_visibility(False)
            second.set_max_length(128)
            second.set_placeholder_text('Confirm password / 비밀번호 확인')
            box.pack_start(second, False, False, 0)
        error = Gtk.Label()
        error.set_line_wrap(True)
        box.pack_start(error, False, False, 0)
        dialog.show_all()
        while dialog.run() == Gtk.ResponseType.OK:
            try:
                if password:
                    if first.get_text() != second.get_text():
                        raise ValueError('Passwords do not match / 비밀번호가 다릅니다.')
                    Config(DATA).set_password(first.get_text())
                    service('restart')
                else:
                    rename(first.get_text())
                break
            except ValueError as exc:
                error.set_text(str(exc))
            except (OSError, subprocess.SubprocessError):
                error.set_text('Could not finish. Check the local service; if the password was saved, restart the dashboard.')
        first.set_text('')
        second.set_text('')
        dialog.destroy()


def main():
    tray = Tray()
    Gtk.main()
    tray.indicator.set_status(Indicator.IndicatorStatus.PASSIVE)


if __name__ == '__main__':
    main()
