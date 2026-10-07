#!/usr/bin/env bash
set -euo pipefail
[[ $(uname -s) == Linux ]] || { echo 'Linux required'; exit 1; }
[[ $(id -u) != 0 ]] || { echo 'Run as your normal Spark user, not root.'; exit 1; }
command -v python3 >/dev/null
python3 -c 'import sys; assert sys.version_info >= (3,12), "Python 3.12+ required"'
systemctl --user show-environment >/dev/null
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
version=$(tr -d '\r\n' < "$source_dir/VERSION")
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Invalid version'; exit 1; }
app="$HOME/.local/share/dgx-spark-control-app"
data="$HOME/.local/share/dgx-spark-control"
mkdir -p "$app/releases" "$data/backups" "$HOME/.config/systemd/user"
chmod 700 "$data"
stamp=$(date +%Y%m%d-%H%M%S-%N)
if [[ -f "$data/config.json" ]]; then cp -p "$data/config.json" "$data/backups/config-$stamp.json"; fi
stage=$(mktemp -d "$app/releases/.stage-XXXXXX")
cp -R "$source_dir/spark_control" "$source_dir/web" "$source_dir/scripts" "$source_dir/docs" "$stage/"
cp "$source_dir/VERSION" "$source_dir/install.sh" "$source_dir/update.sh" "$source_dir/README.md" "$stage/"
python3 -m compileall -q "$stage/spark_control"
old=$(readlink "$app/current" || true)
release="$app/releases/$version-$stamp"
mv "$stage" "$release"
ln -sfn "$release" "$app/current.next"
mv -Tf "$app/current.next" "$app/current"
if [[ -n $old ]]; then ln -sfn "$old" "$app/previous"; fi
cat > "$HOME/.config/systemd/user/dgx-spark-control.service" <<'UNIT'
[Unit]
Description=DGX-SPARK-Control lightweight dashboard
After=network.target
StartLimitIntervalSec=120
StartLimitBurst=3

[Service]
Type=simple
WorkingDirectory=%h/.local/share/dgx-spark-control-app/current
ExecStart=/usr/bin/python3 -m spark_control.server
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
UNIT
systemctl --user daemon-reload
systemctl --user enable --now dgx-spark-control.service
systemctl --user restart dgx-spark-control.service
if ! python3 "$release/scripts/healthcheck.py"; then
  if [[ -n $old && -d $old ]]; then
    ln -sfn "$old" "$app/current.next"
    mv -Tf "$app/current.next" "$app/current"
    systemctl --user restart dgx-spark-control.service
    echo 'Healthcheck failed; previous code restored.' >&2
  else
    systemctl --user stop dgx-spark-control.service
    echo 'Healthcheck failed; service stopped. Check journalctl --user -u dgx-spark-control.' >&2
  fi
  exit 1
fi
echo "Installed DGX-SPARK-Control $version"
echo 'Open http://127.0.0.1:8767 on Spark, or use the Tailscale/SSH instructions in docs/INSTALL.md.'
echo "Access token is stored in $data/access-token (do not publish it)."
echo 'For startup after reboot without login, an administrator may enable loginctl enable-linger for your user.'
