# Updates, migration and recovery / 업데이트·이전·복구

## Package installs / 패키지 설치판

Download the selected release's `dgx-spark-control_X.Y.Z_arm64.deb` and install it:

```bash
sudo apt install ./dgx-spark-control_X.Y.Z_arm64.deb
```

`.deb` owns `/usr/lib/dgx-spark-control` and `/usr/bin/dgx-spark-control`. Personal settings remain under `~/.local/share/dgx-spark-control`. Do not mix `update.sh`/`rollback.sh` with a package install. The old `current` alias points to package code so those commands show a clear guard message.

패키지 설치판은 새 `.deb`로 업데이트합니다. 설정·비밀번호·로그인·모델 등록은 사용자 데이터 디렉터리에 유지합니다. 과거 압축판 업데이트 스크립트와 혼용하지 않습니다.

Updates refresh opted-in users with running user managers, restart only the dashboard and tray, then run an authenticated version-aware health check. The package manager may finish installing files even if a user runtime needs attention; the hook prints a warning. Check `dgx-spark-control setup --check`, service status, and run setup again. Users without a running manager get new code at their next service start. There is no unattended network update agent.

초기 설정이 완료된 사용자의 서버만 다시 시작합니다. 사용자 서버 갱신 실패는 명확한 경고를 출력하며, `dgx-spark-control setup`으로 재시도합니다. 새 패키지 설치가 완료됐다는 메시지만으로 서버가 정상이라고 단정하지 않습니다.

## Archive → package / 기존 압축판에서 이전

1. Install the `.deb`; this alone does not take over an archive installation. `.deb` 설치만으로 기존 서버를 교체하지 않습니다.
2. Open setup, keep both password fields blank, and save. Or, if a password is already configured:

```bash
dgx-spark-control setup --non-interactive
```

3. Verify `--check`, browser access and `systemctl --user status dgx-spark-control`. The backend backs up user units and private settings, replaces only dashboard units, and checks health before recording package management. Password/session/token files are retained.
4. Old versioned code stays in the private app `releases` directory. `previous` points to the pre-migration release; `current` points to `/usr/lib/dgx-spark-control`. Do not delete backups until the new version is verified.

## Recovery / 복구

For future compatible package releases, explicitly install a known-good older package:

```bash
sudo apt install --allow-downgrades ./dgx-spark-control_X.Y.Z_arm64.deb
```

Read the target schema notes first. This release keeps schema 1. No earlier public `.deb` exists before 0.2.0; do not invent a 0.1.2 `.deb` download.

0.2.0 is the first package release. To return to the preserved archive installation after migration, remove the package, then inspect the saved path and run its installer as your normal user:

```bash
sudo apt remove dgx-spark-control
readlink "$HOME/.local/share/dgx-spark-control-app/previous"
```

Confirm that the printed directory is the intended saved release under your app's `releases` directory. Then run `bash /that/verified/release/install.sh`. Do not blindly execute an unverified path. Personal data remains outside the package and is reused. A fresh package-only installation has no prior archive; download and verify a compatible published archive instead.

0.2.0 이전에는 공개 `.deb`가 없습니다. 기존 압축판으로 되돌릴 때는 패키지를 제거하고 `previous`의 실제 경로를 확인한 뒤 그 디렉터리의 `install.sh`를 실행합니다. 설정과 비밀번호는 보존됩니다.

## Removal / 삭제

```bash
sudo apt remove dgx-spark-control
```

Stops/disables active managed dashboards and removes package files. It never deletes models, drivers, Tailscale or the private user data/backups. Logged-out user registrations may remain, guarded by `ConditionPathExists`; they cannot run without package code. Reinstall and run setup to reactivate. Even package purge does not erase private data automatically.

## Archive-only maintenance / 압축판 전용

The archive is retained for existing deployments. Verify its named line in `SHA256SUMS`, extract into an empty directory and run `bash install.sh` as the normal user. Fresh noninteractive installs stop until an interactive password is configured. Optional setup: `python3 -m spark_control.setup --cli --lang ko` (or `en`). GUI setup needs GTK.

```bash
bash ~/.local/share/dgx-spark-control-app/current/update.sh X.Y.Z
bash ~/.local/share/dgx-spark-control-app/current/scripts/rollback.sh
```

These commands are blocked for package-managed installs. Archives use staged versioned code and an authenticated health check; failure restores the prior code link. Never roll back to 0.1.0 if you need password/session support.

## Release checklist / 릴리스 체크리스트

- Align VERSION, CHANGELOG, both quick-start/user guides, architecture and exact validation record.
- Test Linux unit/API behavior, GTK rendering, invalid first-run input, migration, reinstall, recovery, authentication persistence, cgroup budget and browser access.
- Build archive, then `.deb`: `python3 scripts/package.py` and `python3 scripts/build-deb.py` on Linux. The latter needs dpkg-deb, not root. SHA256SUMS contains both files.
- Publish source commit, immutable tag, both assets and SHA256SUMS to GitHub. Re-download and verify the public package, install it, and check runtime.
- Record the same release, commit, guide links, evidence and limitations in the project Notion page.
- Never publish credentials, private model paths, raw telemetry or machine identifiers in packages.
