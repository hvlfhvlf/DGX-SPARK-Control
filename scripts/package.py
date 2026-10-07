"""Create a clean versioned release and a SHA256SUMS file, using only allowlisted paths."""
import hashlib
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
version = (root / 'VERSION').read_text().strip()
output = root / 'dist'
output.mkdir(exist_ok=True)
name = f'DGX-SPARK-Control-{version}.tar.gz'
with tarfile.open(output / name, 'w:gz') as tar:
    for item in ['spark_control', 'web', 'scripts', 'docs', 'tests', 'install.sh', 'update.sh', 'VERSION', 'README.md', 'CHANGELOG.md', 'AGENTS.md']:
        path = root / item
        for file in sorted(path.rglob('*')) if path.is_dir() else [path]:
            if file.is_file() and '__pycache__' not in file.parts and file.suffix != '.pyc':
                tar.add(file, arcname=str(file.relative_to(root)), recursive=False)
checksum = hashlib.sha256((output / name).read_bytes()).hexdigest()
(output / 'SHA256SUMS').write_text(f'{checksum}  {name}\n')
print(output / name)
print(checksum)
