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
if [[ -f "$data/package-managed" ]]; then
  echo 'This installation is managed by .deb. Install the new .deb with apt. / 패키지 설치판은 새 .deb로 업데이트하세요.' >&2
  exit 1
fi
if [[ ! -f "$data/password.json" && ! -t 0 ]]; then
  echo 'Initial password required. Run python3 -m spark_control.setup --cli in an interactive terminal. / 대화형 초기 설정이 필요합니다.' >&2
  exit 2
fi
mkdir -p "$app/releases" "$data/backups" "$HOME/.config/systemd/user"
chmod 700 "$data"
stamp=$(date +%Y%m%d-%H%M%S-%N)
if [[ -f "$data/config.json" ]]; then cp -p "$data/config.json" "$data/backups/config-$stamp.json"; fi
stage=$(mktemp -d "$app/releases/.stage-XXXXXX")
cp -R "$source_dir/spark_control" "$source_dir/web" "$source_dir/scripts" "$source_dir/docs" "$stage/"
cp "$source_dir/VERSION" "$source_dir/install.sh" "$source_dir/update.sh" "$source_dir/README.md" "$stage/"
python3 -m compileall -q "$stage/spark_control"
python3 "$stage/scripts/probe-hardware.py" "$data"
if [[ ! -f "$data/password.json" ]]; then
  if [[ -t 0 ]]; then
    python3 "$stage/scripts/set-password.py" "$data"
  else
    echo 'Non-interactive install: existing token access retained. Set a password later with scripts/set-password.py.'
  fi
fi
old=$(readlink "$app/current" || true)
release="$app/releases/$version-$stamp"
mv "$stage" "$release"
ln -sfn "$release" "$app/current.next"
mv -Tf "$app/current.next" "$app/current"
if [[ -n $old ]]; then ln -sfn "$old" "$app/previous"; fi
cat > "$HOME/.config/systemd/user/dgx-spark-control.slice" <<'SLICE'
[Unit]
Description=DGX-SPARK-Control total resource budget
[Slice]
CPUAccounting=yes
MemoryAccounting=yes
MemoryHigh=256M
MemoryMax=480M
MemorySwapMax=0
SLICE
cat > "$HOME/.config/systemd/user/dgx-spark-control.service" <<'UNIT'
[Unit]
Description=DGX-SPARK-Control lightweight dashboard
After=network.target
StartLimitIntervalSec=120
StartLimitBurst=3

[Service]
Type=simple
Slice=dgx-spark-control.slice
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
cat > "$HOME/.config/systemd/user/dgx-spark-control-tray.service" <<'TRAY'
[Unit]
Description=DGX-SPARK-Control local desktop tray
PartOf=graphical-session.target
After=graphical-session.target
StartLimitIntervalSec=120
StartLimitBurst=3
[Service]
Type=simple
Slice=dgx-spark-control.slice
WorkingDirectory=%h/.local/share/dgx-spark-control-app/current
ExecStart=/usr/bin/python3 -m spark_control.tray
Environment=PYTHONDONTWRITEBYTECODE=1
MemoryAccounting=yes
MemoryMax=128M
MemorySwapMax=0
TasksMax=32
UMask=0077
NoNewPrivileges=yes
Restart=on-failure
RestartSec=10
TRAY
mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/dgx-spark-control-tray.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=DGX-SPARK-Control
Comment=Local dashboard settings and password recovery
Exec=/bin/bash "$app/current/scripts/start-tray.sh"
Terminal=false
X-GNOME-Autostart-enabled=true
DESKTOP
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
if systemctl --user is-active --quiet graphical-session.target && python3 -c 'import gi; gi.require_version("Gtk", "3.0"); gi.require_version("AyatanaAppIndicator3", "0.1")' 2>/dev/null; then
  systemctl --user restart dgx-spark-control-tray.service || true
else
  echo 'Desktop tray available after GTK/AppIndicator setup and desktop login; see docs/DESKTOP.md.'
fi
echo "Installed DGX-SPARK-Control $version"
echo 'Open http://127.0.0.1:8767 on Spark, or use the Tailscale/SSH instructions in docs/INSTALL.md.'
echo 'Sign in with your installation password. For local password recovery, see docs/DESKTOP.md.'
echo "Private maintenance token is stored in $data/access-token (do not publish it)."
echo 'For startup after reboot without login, an administrator may enable loginctl enable-linger for your user.'
