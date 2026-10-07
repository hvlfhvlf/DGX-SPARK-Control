"""Set a local dashboard password without printing it or passing it on the command line."""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spark_control.config import Config

directory = sys.argv[1] if len(sys.argv) > 1 else str(Path.home()/'.local/share/dgx-spark-control')
if not sys.stdin.isatty():
    raise SystemExit('Use an interactive terminal; never put the password in command-line arguments.')
first = getpass.getpass('Dashboard password (4-128 characters): ')
second = getpass.getpass('Confirm password: ')
if first != second:
    raise SystemExit('Passwords did not match; no password changed.')
Config(directory).set_password(first)
print('Password hash saved. Restart the dashboard service to invalidate existing sessions.')
