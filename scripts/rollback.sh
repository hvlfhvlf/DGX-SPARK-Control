#!/usr/bin/env bash
set -euo pipefail
app="$HOME/.local/share/dgx-spark-control-app"
target=$(readlink "$app/previous")
[[ -d $target && $target == "$app/releases/"* ]] || { echo 'No previous release'; exit 1; }
current=$(readlink "$app/current")
ln -sfn "$target" "$app/current.next"
mv -Tf "$app/current.next" "$app/current"
systemctl --user restart dgx-spark-control.service
if ! python3 "$app/current/scripts/healthcheck.py"; then
  ln -sfn "$current" "$app/current.next"
  mv -Tf "$app/current.next" "$app/current"
  systemctl --user restart dgx-spark-control.service
  echo 'Rollback failed, restored previous current release' >&2
  exit 1
fi
ln -sfn "$current" "$app/previous"
if systemctl --user is-active --quiet dgx-spark-control-tray.service; then
  if [[ -f "$app/current/spark_control/tray.py" ]]; then
    systemctl --user restart dgx-spark-control-tray.service
  else
    systemctl --user stop dgx-spark-control-tray.service
  fi
fi
echo 'Code rollback complete; settings retained. See docs/UPDATES.md for schema compatibility.'
