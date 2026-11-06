# Service updates / 서비스 업데이트

Available in 0.3.3. Supported opt-in installs: versioned official Harness npm releases, official Hermes source checkout, official ComfyUI source checkout with `.venv`. The browser cannot supply paths, commands, package names or URLs. Updates do not run in the dashboard cgroup and do not start or stop apps automatically.

0.3.3에서 제공하는 선택적 기능입니다. 공식 설치본과 기존 systemd 사용자 서비스를 로컬에서 연결해야 합니다. 설치 검색만으로 업데이트 권한을 자동 부여하지 않습니다. 앱 버전과 모델 가중치 버전은 별개입니다.

## Local binding / 로컬 연결

An authorized local operator creates `service-updates.json` in the dashboard's private data directory, mode 0600. Example (replace placeholders **locally**, never publish the real file):

```json
{
  "example-service": {
    "kind": "comfyui",
    "profile_id": "example-profile",
    "units": ["example-comfy.service"],
    "root": "/home/USER/ComfyUI",
    "channel": "stable"
  }
}
```

- `kind`: `harness`, `hermes`, `comfyui`. Profile and units must exactly match the registered service and all its profiles must allow control.
- Hermes also needs `data` (HERMES_HOME); its official launcher is `root/.hermes/bin/hermes` and the complete managed runtime under HERMES_HOME is included. Harness needs `data` (DSH_HOME) and the absolute `node` binary inside its existing runtime. Harness root must already contain `active-version.txt` and versioned `releases/<version>/node_modules/@deepseek-ai/dsh`.
- Source channels: `stable` selects the latest non-prerelease GitHub release; `main` follows Hermes main / ComfyUI master. Preserve the existing channel: do not silently switch canary/development users to older stable. Downgrades and divergent histories are rejected. Harness follows the official npm latest tag, which can itself be a prerelease.
- Source origin must be the exact official HTTPS GitHub repository. Tracked local changes block updates. Symlinked app roots and cross-filesystem backup targets need local review and are rejected.
- Use an existing, verified launch unit. Additional manually launched processes using the installation block updates.

Install the **start guards** as the normal service owner, from the installed code directory:

```bash
cd /usr/lib/dgx-spark-control
python3 -m spark_control.service_updates guards --directory "$HOME/.local/share/dgx-spark-control"
```

This adds `90-spark-update-guard.conf` under each selected user unit's drop-in directory and reloads systemd; it does not restart apps. The condition prevents unit starts while the global update lock exists. Do not remove this lock to bypass an incomplete recovery.

로컬 연결 파일 작성 후 위 명령으로 시작 보호 조건을 설치합니다. 기존 서비스 실행 명령·환경 파일은 교체하지 않습니다. 업데이트·복구 중 시작을 차단하며, 실패 복구가 끝나지 않았다면 잠금 파일을 임의 삭제하지 마세요.

## Operation and recovery / 동작·복구

1. Details → Check for updates: explicit official metadata request. No background network updater. Review tickets expire after 30 minutes and invalidate when installed version, registry revision or bindings change.
2. Stop the service yourself. Update → Back up & update. The API rechecks all processes and blocks if running, unknown or transitioning.
3. A single transient user unit takes the shared registry lock, checks disk space, copies private backups, installs and validates. It has 2 GiB RAM / no swap / 150% CPU / 128 tasks / one-hour limit, separate from the dashboard's 480 MiB combined cap. It has no persistent resident agent.
4. Success stays **stopped**. Start from Model Bay and check app API, plugins, provider and normal workflow yourself. Basic CLI/import/pip checks are not a generation or conversation test.
5. Failure restores snapshots; failed trees are quarantined with `.update-failed-*` names. Backups live under `service-update-backups/<job-id>` and contain private data. Keep them until the new version works. They are not uploaded or bundled.
6. Worker failure/timeout runs recovery through `ExecStopPost`. Host power loss can prevent that hook; the retained guard blocks starts. After inspecting the private job record, an operator may resume recovery:

```bash
cd /usr/lib/dgx-spark-control
python3 -m spark_control.service_updates recover --directory "$HOME/.local/share/dgx-spark-control"
```

Restore requires app units and manual processes to be stopped. If restore itself fails, the lock remains and local intervention is required. Never describe a failed recovery as restored. Snapshot scope excludes external workspaces, external databases and symlink targets; those need their own backups.

실패 시 코드뿐 아니라 복사한 실행 환경·앱 상태를 복구합니다. 복구 실패·전원 중단 후에는 로컬 확인이 필요할 수 있습니다. 서비스는 자동 시작하지 않습니다. 백업에 없는 외부 작업 폴더·외부 DB·심볼릭 링크 대상은 별도 백업 대상입니다.

## Per app / 앱별 범위

- **Harness:** official exact npm version with reviewed integrity; old release retained, active version pointer and DSH_HOME copied. No automatic provider inference/test prompt or token disclosure. Restart may rotate the app's login token; existing authenticated app handoff reads the fresh URL.
- **Hermes:** official `update --yes --no-gateway-restart --channel ...`; full HERMES_HOME plus code/env if outside it. Review config/plugin migration warnings locally. The official doctor runs before/after installation without --fix or --live. A newly failing doctor rolls back; if both checks fail, completion is flagged for local review (it does not claim the warnings are identical or that the app is healthy). If upstream advances during installation, exact target mismatch causes recovery instead of accepting an unreviewed version.
- **ComfyUI:** exact official commit, requirements sync with installed Torch/vision/audio versions constrained. Code, `.venv` and local config are backed up. Models/input/output/temp/custom_nodes are preserved in place and not updated; custom-node dependency compatibility still needs workflow validation. No CUDA/driver changes.

## API and privacy

Authenticated `GET /api/services/update?id=ID` only reads local installed/cached status. POST `.../check` accepts ID; POST `.../apply` accepts ID and opaque review ticket. Fixed error codes and phases reach the browser; local paths, command output, tokens, prompts, configuration bodies and backup contents do not. GET cannot update. Same-origin protections and the existing session model apply.

## Backup retention

Checking versions never creates backups. Successful validated updates retain one managed recovery snapshot per service. Old copies are pruned only after validation. Failed/review-required maintenance retains evidence and blocks further updates until local review. Clear review_required only after inspecting the snapshot and quarantined tree. Partial pre-mutation copies are discarded. Harness keeps current/previous updater-owned releases; manual releases are untouched. Free-space checks include temporary copy/restore headroom.
