#!/usr/bin/env bash
set -euo pipefail
# Invoked by desktop autostart after the graphical session exports its environment.
systemctl --user import-environment DISPLAY WAYLAND_DISPLAY XAUTHORITY XDG_CURRENT_DESKTOP 2>/dev/null || true
systemctl --user start dgx-spark-control-tray.service
