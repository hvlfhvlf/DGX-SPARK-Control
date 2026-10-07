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
echo 'Code rollback complete; settings retained. See docs/UPDATES.md for schema compatibility.'
