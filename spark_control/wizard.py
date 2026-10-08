"""Small, on-demand GTK3 setup wizard. No embedded browser or background agent."""
import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from . import setup
from .desktop import connection, open_url, LOCAL_URL

TEXT = {
 'en': {
  'title': 'Set up your Spark', 'intro': 'A lightweight dashboard. A few settings. Ready to connect.',
  'welcome': '01 / WELCOME', 'account': '02 / YOUR SPARK', 'network': '03 / CONNECTION', 'finish': '04 / READY',
  'requirements': 'Ubuntu 24.04 · ARM64 · Python 3.12+\nServer + tray memory limit: 480 MiB.\nExisting models, drivers and Tailscale routes stay in place.',
  'existing': 'Existing installation detected. Your password and remembered device logins will be kept.',
  'fresh': 'Choose a display name and a password for browser access.',
  'name': 'Spark display name', 'password': 'Password (4–128 characters)', 'confirm': 'Confirm password',
  'keep': 'Leave both password fields empty to keep your password. Changing it signs out existing devices.',
  'private': 'The display name does not change your computer name or connection address.',
  'connected': 'Tailscale access is already configured:',
  'local': 'Local access will be ready after setup. Tailscale access needs a separate connection step.',
  'netnote': 'Only devices allowed on your Tailscale network can use its HTTPS address.\nSetup will not replace an existing route or enable public sharing.',
  'help': 'Connection instructions', 'refresh': 'Check again', 'back': 'Back', 'next': 'Continue', 'apply': 'Save & start',
  'working': 'Saving settings and checking the dashboard…', 'done': 'Your dashboard is ready.',
  'open': 'Open dashboard', 'copy': 'Copy address', 'copied': 'Address copied', 'close': 'Close',
  'tray': 'Use the desktop tray to reopen setup or recover your password. Closing this window leaves the dashboard running.',
  'traywarning': 'If no tray icon appears, enable Ubuntu AppIndicators in GNOME Extensions. You can still use the browser.',
  'guide': 'First check: tailscale serve status\n\nIf Tailscale is not connected, install it from tailscale.com/download/linux and sign in.\nAfter setup, if HTTPS port 443 is unused, run:\nsudo tailscale serve --bg --https=443 http://127.0.0.1:8767\n\nIf prompted, complete HTTPS/Serve approval in your Tailscale account. Keep existing routes. If 443 is occupied, use an available 8443 port and include it in the URL. Do not enable Funnel.\n\nTo start the dashboard before desktop login:\nsudo loginctl enable-linger "$USER"\nThe tray starts after desktop login.',
  'retry': 'Could not finish. Your model services were not changed. Check the message below and retry.',
 },
 'ko': {
  'title': 'Spark 시작하기', 'intro': '가벼운 대시보드. 몇 가지 설정으로 접속 준비를 마칩니다.',
  'welcome': '01 / 시작', 'account': '02 / 나의 SPARK', 'network': '03 / 연결', 'finish': '04 / 완료',
  'requirements': 'Ubuntu 24.04 · ARM64 · Python 3.12 이상\n서버 + 트레이 메모리 상한: 480 MiB\n기존 모델·드라이버·Tailscale 연결 설정을 유지합니다.',
  'existing': '기존 설치를 발견했습니다. 비밀번호와 기기 로그인 정보를 유지합니다.',
  'fresh': '화면에 표시할 이름과 브라우저 접속 비밀번호를 정하세요.',
  'name': 'Spark 표시 이름', 'password': '비밀번호 (4–128자)', 'confirm': '비밀번호 확인',
  'keep': '두 비밀번호 칸을 비우면 기존 비밀번호를 유지합니다. 변경하면 기존 기기의 로그인이 해제됩니다.',
  'private': '표시 이름을 바꿔도 컴퓨터 이름이나 접속 주소는 바뀌지 않습니다.',
  'connected': 'Tailscale 접속이 이미 설정되어 있습니다:',
  'local': '설정 완료 후 Spark에서 바로 접속할 수 있습니다. Tailscale 접속은 별도 연결 단계가 필요합니다.',
  'netnote': 'Tailscale 네트워크에서 접근이 허용된 기기만 HTTPS 주소를 이용합니다.\n기존 연결을 덮어쓰거나 인터넷 공개를 활성화하지 않습니다.',
  'help': '연결 설정 안내', 'refresh': '다시 확인', 'back': '이전', 'next': '계속', 'apply': '저장하고 시작',
  'working': '설정을 저장하고 서버 상태를 확인하고 있습니다…', 'done': '대시보드가 준비되었습니다.',
  'open': '대시보드 열기', 'copy': '주소 복사', 'copied': '주소를 복사했습니다', 'close': '닫기',
  'tray': '데스크톱 트레이에서 초기 설정을 다시 열거나 비밀번호를 복구할 수 있습니다. 창을 닫아도 서버는 계속 실행됩니다.',
  'traywarning': '트레이가 보이지 않으면 GNOME 확장에서 Ubuntu AppIndicators를 켜세요. 브라우저 접속은 계속 사용할 수 있습니다.',
  'guide': '먼저 확인: tailscale serve status\n\nTailscale 미연결 시 tailscale.com/download/linux에서 설치하고 로그인하세요.\n초기 설정을 마친 후 HTTPS 443 포트가 비어 있을 때만 실행하세요:\nsudo tailscale serve --bg --https=443 http://127.0.0.1:8767\n\n안내가 나오면 Tailscale 계정에서 HTTPS/Serve 활성화를 완료하세요. 기존 연결을 유지하세요. 443이 사용 중이면 비어 있는 8443 포트를 사용하고 주소에 포트를 포함하세요. Funnel은 켜지 않습니다.\n\n데스크톱 로그인 전에도 서버를 시작하려면:\nsudo loginctl enable-linger "$USER"\n트레이는 데스크톱 로그인 후 실행됩니다.',
  'retry': '설정을 완료하지 못했습니다. 모델 서비스는 변경하지 않았습니다. 아래 내용을 확인하고 다시 시도하세요.',
 }
}


class Wizard(Gtk.Window):
    def __init__(self, language='en'):
        super().__init__(title='DGX-SPARK-Control Setup')
        self.set_default_size(660, 620)
        self.set_border_width(28)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_from_file(str(setup.ROOT/'web/icon.svg'))
        self.connect('delete-event', self.on_close)
        self.connect('destroy', lambda *_: Gtk.main_quit())
        self.language = language if language in TEXT else 'en'
        self.current = setup.state()
        self.connection = connection()
        self.page = 0
        self.busy = False
        self.bindings = []
        self.entries = {}
        css = Gtk.CssProvider()
        css.load_from_data(b'window { background: #111510; color: #edf0e5; } label { color: #edf0e5; } .step { color: #c5ff00; font-weight: bold; } .title { font-size: 26px; font-weight: bold; } button { padding: 9px 16px; } button.suggested-action { background: #c5ff00; color: #111510; border: none; } button.suggested-action label { color: #111510; } button:disabled { opacity: 0.45; } entry { padding: 10px; }')
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.add(outer)
        top = Gtk.Box(spacing=12)
        logo = Gtk.Label(label='SPARK CONTROL / '+setup.VERSION)
        logo.get_style_context().add_class('step')
        top.pack_start(logo, True, True, 0)
        combo = Gtk.ComboBoxText()
        self.language_picker = combo
        combo.append('en', 'English')
        combo.append('ko', '한국어')
        combo.set_active_id(self.language)
        combo.connect('changed', self.change_language)
        top.pack_end(combo, False, False, 0)
        outer.pack_start(top, False, False, 0)
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, transition_duration=150)
        outer.pack_start(self.stack, True, True, 0)
        for number, key in enumerate(('welcome', 'account', 'network', 'finish')):
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
            self.label(box, key, 'step')
            self.stack.add_named(box, str(number))
            if number == 0:
                self.label(box, 'title', 'title')
                self.label(box, 'intro')
                self.label(box, 'requirements')
                self.label(box, 'existing' if self.current['has_password'] else 'fresh')
            elif number == 1:
                for field in ('name', 'password', 'confirm'):
                    field_label = self.label(box, field)
                    entry = Gtk.Entry()
                    field_label.set_mnemonic_widget(entry)
                    entry.set_max_length(32 if field == 'name' else 128)
                    entry.set_visibility(field == 'name')
                    if field == 'name':
                        entry.set_text(self.current['name'])
                    box.pack_start(entry, False, False, 0)
                    self.entries[field] = entry
                self.label(box, 'keep' if self.current['has_password'] else 'private')
            elif number == 2:
                self.net_label = self.label(box, 'netnote')
                self.net_status = Gtk.Label(xalign=0, selectable=True, wrap=True)
                box.pack_start(self.net_status, False, False, 0)
                self.button(box, 'refresh', self.refresh)
                self.button(box, 'help', self.help)
            else:
                self.label(box, 'done', 'title')
                self.address = Gtk.Label(xalign=0, selectable=True, wrap=True)
                box.pack_start(self.address, False, False, 0)
                self.button(box, 'open', lambda *_: open_url(LOCAL_URL))
                self.button(box, 'copy', self.copy)
                self.button(box, 'help', self.help)
                self.label(box, 'tray')
                self.label(box, 'traywarning')
        self.error = Gtk.Label(xalign=0, wrap=True, selectable=True)
        outer.pack_start(self.error, False, False, 0)
        footer = Gtk.Box(spacing=12)
        self.back = Gtk.Button()
        self.back.connect('clicked', self.previous)
        footer.pack_start(self.back, False, False, 0)
        self.next = Gtk.Button()
        self.next.get_style_context().add_class('suggested-action')
        self.next.connect('clicked', self.advance)
        footer.pack_end(self.next, False, False, 0)
        outer.pack_end(footer, False, False, 0)
        self.translate()
        self.show_all()

    def label(self, box, key, style=None):
        label = Gtk.Label(xalign=0, wrap=True)
        label.set_max_width_chars(62)
        if style:
            label.get_style_context().add_class(style)
        box.pack_start(label, False, False, 0)
        self.bindings.append((label.set_text, key))
        return label

    def button(self, box, key, callback):
        button = Gtk.Button()
        button.connect('clicked', callback)
        box.pack_start(button, False, False, 0)
        self.bindings.append((button.set_label, key))

    def translate(self):
        for setter, key in self.bindings:
            setter(TEXT[self.language][key])
        self.back.set_label(TEXT[self.language]['back'])
        self.next.set_label(TEXT[self.language]['close' if self.page == 3 else 'apply' if self.page == 2 else 'next'])
        self.back.set_sensitive(self.page in (1, 2) and not self.busy)
        self.net_status.set_text((TEXT[self.language]['connected']+'\n'+self.connection['url']) if self.connection['url'] else TEXT[self.language]['local'])

    def change_language(self, combo):
        self.language = combo.get_active_id()
        self.translate()

    def previous(self, *_):
        self.page -= 1
        self.stack.set_visible_child_name(str(self.page))
        self.error.set_text('')
        self.translate()

    def advance(self, *_):
        if self.page == 3:
            self.destroy()
            return
        if self.page == 1:
            try:
                setup.validate(*(self.entries[k].get_text() for k in ('name', 'password', 'confirm')), self.current['has_password'])
            except ValueError as exc:
                self.error.set_text(str(exc))
                return
        if self.page == 2:
            self.busy = True
            self.next.set_sensitive(False)
            self.back.set_sensitive(False)
            self.error.set_text(TEXT[self.language]['working'])
            values = [self.entries[k].get_text() for k in ('name', 'password', 'confirm')]
            def worker():
                try:
                    result = setup.configure(*values, self.language)
                    GLib.idle_add(self.finished, result, None)
                except Exception as exc:
                    GLib.idle_add(self.finished, None, str(exc))
            threading.Thread(target=worker, daemon=True).start()
            return
        self.page += 1
        self.error.set_text('')
        self.stack.set_visible_child_name(str(self.page))
        self.translate()

    def finished(self, result, error):
        self.busy = False
        self.next.set_sensitive(True)
        if error:
            self.error.set_text(TEXT[self.language]['retry']+'\n'+error)
            # A failed service start may still have saved the password.
            self.current = setup.state()
        else:
            self.connection = result['tailscale']
            self.entries['password'].set_text('')
            self.entries['confirm'].set_text('')
            self.page = 3
            self.address.set_text(LOCAL_URL+'\n'+(self.connection['url'] or TEXT[self.language]['local']))
            self.error.set_text('')
            self.stack.set_visible_child_name('3')
        self.translate()
        return False

    def refresh(self, *_):
        self.connection = connection()
        self.translate()

    def help(self, *_):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.CLOSE, text=TEXT[self.language]['help'])
        dialog.format_secondary_text(TEXT[self.language]['guide'])
        for child in dialog.get_message_area().get_children():
            if isinstance(child, Gtk.Label):
                child.set_selectable(True)
        dialog.run()
        dialog.destroy()

    def copy(self, *_):
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(self.connection['url'] or LOCAL_URL, -1)
        Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).store()
        self.error.set_text(TEXT[self.language]['copied'])

    def on_close(self, *_):
        return self.busy


def main(language='en'):
    if not Gtk.init_check()[0]:
        raise RuntimeError('No desktop display. Run dgx-spark-control setup --cli / 데스크톱이 없으면 --cli를 사용하세요.')
    Wizard(language)
    Gtk.main()
