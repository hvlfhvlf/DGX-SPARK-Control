"""One-time installer inventory. Never prompts for privilege or stores serial numbers."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from spark_control.hardware import parse_installed_memory

directory = Path(sys.argv[1])
installed = None
decoder = shutil.which('dmidecode')
if decoder:
    commands = [[decoder, '--type', '17']]
    # Existing passwordless/cached permission only. No sudo prompt or policy change.
    if shutil.which('sudo'):
        commands.append(['sudo', '-n', decoder, '--type', '17'])
    for command in commands:
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                installed = parse_installed_memory(result.stdout)
                if installed:
                    break
        except (OSError, subprocess.TimeoutExpired):
            pass
temporary = directory / 'hardware.tmp'
fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as stream:
    json.dump({'installed_memory_bytes': installed}, stream)
os.replace(temporary, directory / 'hardware.json')
print('Hardware inventory saved; missing firmware capacity uses OS-reported memory.')
