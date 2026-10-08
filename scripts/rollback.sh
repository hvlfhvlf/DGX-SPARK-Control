#!/usr/bin/env bash
set -euo pipefail
if [[ -f "$HOME/.local/share/dgx-spark-control/package-managed" ]]; then
  echo 'Managed by .deb: install a compatible earlier .deb with apt --allow-downgrades. / 호환되는 이전 .deb로 복구하세요.' >&2
  exit 1
fi
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
