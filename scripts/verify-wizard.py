"""Render our own GTK widget tree offscreen; never capture or control the desktop.

Run on a GTK-capable build host: DISPLAY=:0 python3 scripts/verify-wizard.py OUTPUT
Uses fixtures and a temporary HOME, without starting production services.
"""
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spark_control import wizard, setup
from gi.repository import Gtk

output = Path(sys.argv[1])
output.mkdir(parents=True, exist_ok=True)
fixture = {'version': setup.VERSION, 'name': 'MY SPARK', 'has_password': False, 'managed': False, 'language': 'en'}
with patch.object(setup, 'state', return_value=fixture), patch.object(wizard, 'connection', return_value={'url': None, 'state': 'needs_setup'}), patch.object(Gtk.Window, 'show_all'):
    view = wizard.Wizard('en')
child = view.get_child()
view.remove(child)
offscreen = Gtk.OffscreenWindow()
offscreen.set_border_width(28)
offscreen.set_default_size(660, 620)
offscreen.add(child)
offscreen.show_all()

def capture(name):
    # Allow GTK style/allocation and the short stack transition to complete.
    deadline = time.monotonic()+.25
    while time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(.01)
    pixbuf = offscreen.get_pixbuf()
    assert pixbuf is not None
    pixbuf.savev(str(output/name), 'png', [], [])

for lang in ('en', 'ko'):
    view.language_picker.set_active_id(lang)
    for page in range(3):
        view.page = page
        view.stack.set_visible_child_name(str(page))
        view.translate()
        capture(f'setup-{lang}-{page+1}.png')

# First-run validation must block progress. Success path uses a mocked installer.
view.page = 1
view.advance()
assert view.page == 1 and view.error.get_text()
view.entries['password'].set_text('test-only-password')
view.entries['confirm'].set_text('test-only-password')
view.advance()
assert view.page == 2
result = {'ok': True, 'tailscale': {'url': None, 'state': 'needs_setup'}}
with patch.object(setup, 'configure', return_value=result) as apply:
    view.advance()
    deadline = time.monotonic()+3
    while view.busy and time.monotonic() < deadline:
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
        time.sleep(.01)
    apply.assert_called_once()
assert view.page == 3 and not view.entries['password'].get_text()
capture('setup-ko-complete.png')
print('GTK offscreen renders + validation + mocked installation transition passed')
