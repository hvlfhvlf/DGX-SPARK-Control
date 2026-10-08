#!/usr/bin/env bash
set -euo pipefail
if [[ -f "$HOME/.local/share/dgx-spark-control/package-managed" ]]; then
  echo 'Managed by .deb: download the new package and install with apt. / 새 .deb 패키지로 업데이트하세요.' >&2
  exit 1
fi
version="${1:-0.2.0}"
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Usage: bash update.sh X.Y.Z'; exit 1; }
temp=$(mktemp -d)
trap 'rm -rf -- "$temp"' EXIT
base="https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/download/v$version"
curl --fail --location --proto '=https' --tlsv1.2 "$base/DGX-SPARK-Control-$version.tar.gz" -o "$temp/release.tar.gz"
curl --fail --location --proto '=https' --tlsv1.2 "$base/SHA256SUMS" -o "$temp/SHA256SUMS"
python3 - "$temp" "$version" <<'PY'
import hashlib, pathlib, sys, tarfile
root, version = pathlib.Path(sys.argv[1]), sys.argv[2]
filename = f'DGX-SPARK-Control-{version}.tar.gz'
entries = [line.split() for line in (root/'SHA256SUMS').read_text().splitlines()]
expected = next(parts[0] for parts in entries if len(parts) == 2 and parts[1].lstrip('*') == filename)
actual = hashlib.sha256((root/'release.tar.gz').read_bytes()).hexdigest()
if actual != expected: raise SystemExit('Release checksum mismatch')
with tarfile.open(root/'release.tar.gz') as archive:
    for item in archive.getmembers():
        target=(root/'source'/item.name).resolve()
        if not target.is_relative_to((root/'source').resolve()) or not (item.isfile() or item.isdir()):
            raise SystemExit('Unsafe archive entry')
    archive.extractall(root/'source', filter='data')
PY
bash "$temp/source/install.sh"
