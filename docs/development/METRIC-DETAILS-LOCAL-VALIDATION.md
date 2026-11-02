# Private Spark validation / 비공개 Spark 적용 검증

Date: 2026-11-02, Asia/Seoul. The owner authorized installation on Spark and real-data verification, while explicitly withholding GitHub publication. This is a private development build, not a public release.

These records describe the preceding detail-only builds through `0.2.2~dev20261102.3`. The current combined service/detail candidate is documented in `../releases/0.3.0~rc1.md`. Earlier evidence and artifact hashes remain intact.

## Detail cleanup: 0.2.2~dev20261102.3

- Package SHA256: `30d799cfca029ac97117c9579ecdf55c4e6f33687301935c389043c2e98c8a88`.
- Network/I/O device lists, scope, units and sampling explanations now appear only inside the existing collapsed notes. The same review moved CPU/memory calculation text, sensor raw identifiers, memory-clock capability and power-measurement explanations below the fold. Live per-core readings, sensor temperatures/source families, installed versus OS-usable capacity and limiting events remain visible. Repeated architecture and range statistics were removed; GPU-only power scope stays explicit. SSD retains the preceding capacity-only layout.
- Verified all eight live dialogs at 1440, 390 and 320 px in Korean, and all eight expanded disclosures at 320 px in English. Four/two headline columns, no horizontal modal overflow or clipped headline readings; SSD has no chart, the other seven retain their charts. Browser error/warning log was empty. Mobile evidence is Chromium viewport testing, not physical Safari validation.
- During 40 seconds of real network updates, expanded notes, keyboard focus and scroll position stayed unchanged. The technical content remained inside the same disclosure. Unsupported memory clock remains unavailable; actual rates include zero and small nonzero values.
- Existing Node tests 7/7 and Linux tests 17/17 passed; JavaScript/shell syntax and git whitespace checks passed. Installed assets match the source snapshot; backend and original chip art are unchanged. No additional polling or monitoring process was introduced.
- Applied through dpkg with a private rollback package retained. Config/password/session/token byte hashes and display name match the pre-update baseline. All 50 other running user services retained their processes. Dashboard/tray memory immediately after update was 56,094,720 bytes (about 53.5 MiB), with the unchanged 480 MiB cap and zero swap allowance; this is not an inference overhead benchmark.
- Evidence/package live outside the repository in `verification/detail-cleanup-20261102`. No GitHub commit/push/release. This is a post-build validation record; source guides/specification were subsequently updated to identify the verified revision without rebuilding the tested artifact.

## SSD follow-up: 0.2.2~dev20261102.2

- Package SHA256: `24d23135c92b853f7ee325619aec4e805de36789eed17676cabaa36bbbef83d7`.
- SSD capacity no longer renders history, time-range controls, averages or peaks. It retains four current readings, used/available/reserved composition and the mount point. Capacity accounting and calculation notes are collapsed by default; their values still refresh without replacing the disclosure.
- Verified on the actual private Spark HTTPS page: four headline values, no SSD history/range controls, separate df percentage in the expanded notes, and preserved disclosure/focus/scroll across 70 seconds of live updates. The other seven dialogs still have charts and all three range controls.
- Korean and English UI checked. Phone widths 390 and 320 pixels retain two summary columns with no clipped values or horizontal overflow. Desktop modal now fits its capacity content instead of allocating a history panel. Physical Safari testing remains outside this check.
- Existing Node tests 7/7 and Linux tests 17/17 passed; JavaScript and shell syntax checks passed. All installed web hashes match the staged build; backend and original chip art remain unchanged.
- Installed through dpkg, retaining a private rollback package for the preceding development build. Config/password/session/token hashes and display name stayed unchanged; the same 50 unrelated user services retained their processes. The previously validated package rollback mechanism is unchanged; no additional rollback round trip was needed for this UI-only revision.
- Fresh evidence and the private package are outside the repository under `verification/ssd-detail-20261102`. No commit, push, public release or extra collector was introduced. This section records post-build validation and does not alter the package checksum above.

## Build identity

- Installed package: `dgx-spark-control_0.2.2~dev20261102.1_arm64.deb`.
- SHA256: `5a1dffe803d3e9d91fd94f2226a84362be45146e66fe36cc738f7898e06da429`.
- Base commit: `abb95c963c88a24001f9035254612a3a476b3cc0`, plus the uncommitted metric-detail implementation. No commit, tag, push or GitHub Release was created.
- The staging copy overrides `VERSION` and adds a private-build notice. Repository `VERSION` and stable installation instructions remain at 0.2.1 pending an explicit release decision. The package includes `docs/LOCAL-BUILD.json` with source file hashes identifying the build snapshot.
- The staging archive uses an explicit source allowlist and normalized owner metadata. Local fixtures, screenshots, telemetry logs, credentials and deployment scripts are outside the repository and were not packaged.
- All installed web asset hashes matched the build source. Backend Python files match the previous installed version. The original chip SVG is unchanged. This report is a post-build verification record; it does not change the recorded package checksum.

## Actual installation and recovery

- Backed up private settings locally on Spark and reconstructed a rollback package from the existing 0.2.1 installation. The backup directory is private and outside package-managed code.
- Used dpkg for the existing package installation; no archive updater or manually overwritten installed files.
- Verified update to the development package, downgrade to 0.2.1, and reapplication of the development package. Authenticated health/version checks passed after each operation.
- Config, password record, saved-session record and maintenance-token byte hashes remained identical. The display name was preserved. The browser resumed the existing login without another password prompt.
- The 50 previously running user services other than dashboard/tray retained their process IDs and start timestamps. No model start/stop action was issued.
- Dashboard and tray are active. Dashboard automatic startup remains enabled; tray retains its existing graphical-session/autostart mechanism. The operating system was not rebooted for this frontend change.

## Real measurements and UI

- Opened all eight detail dialogs through the Spark's existing private Tailscale HTTPS origin. Each received `source: live`; the served page contains no preview fixture script.
- GPU usage, temperature, power and SM clock agreed with a nearby `nvidia-smi` reading at idle: 0%, 34 C, approximately 9 W and 2171 MHz. These are observations at verification time, not performance specifications.
- Memory displayed approximately 8.0 GiB used out of 121.7 GiB OS usable capacity; firmware capacity remains separately displayed as 128 GiB. Unavailable memory-clock data displays unavailable rather than zero.
- SSD displayed approximately 1.05 TiB used, 2.35 TiB user-available and 3.58 TiB filesystem total. The 29.4% used/total and 31% Linux df values were distinguished correctly; df's denominator excludes reserved space.
- CPU details rendered the 20 reported logical cores. Temperature details rendered NVML GPU plus 11 hwmon readings with their actual driver identity; this does not imply 12 distinct physical components or known CPU/SoC locations.
- Network and disk I/O showed actual zero and small nonzero rates, including three-decimal MB/s values below 1. Graphs used collected history and gaps, without generated wave data.
- All eight dialogs checked at 1440px desktop and 390/320px phone widths: four/two summary columns respectively, no horizontal modal overflow and no clipped headline values.
- During approximately 40 seconds of live updates, the selected 1-minute range, open notes, keyboard focus and scroll position stayed unchanged. Escape closed the dialog. Browser error/warning log was empty at the checked state.
- Restarting the dashboard clears its in-memory history. New samples accumulate afterward; a short trace immediately after installation is expected.

## Resource and regression checks

- Node calculation tests: 7/7 passed. All web JavaScript syntax checks passed. Linux unit/API tests: 17/17 passed. Install/update/rollback shell syntax checks passed.
- Eight successive metrics requests reused one sample and added one collection. With no dashboard client polling, collection count stayed at 47 for a 12-second observation.
- Dashboard/tray combined current memory was 57,815,040 bytes (about 55.1 MiB) during the live check. The existing cgroup lifetime peak was 70,336,512 bytes, including activity before this update; it is not a build-specific benchmark.
- Memory maximum remains 503,316,480 bytes (480 MiB), swap maximum 0, and observed memory-limit/OOM event counters were zero. No additional collector, timer, dependency or service was installed.

## Evidence and limits

Private evidence lives outside source in the local `verification/spark-live-20261102` directory: build manifest/package, deployment checks, live desktop/mobile captures and geometry records. Personal addresses, raw telemetry and private backup paths are intentionally absent here.

This was an existing-machine update with live idle/light-activity telemetry, not a clean-machine installation or controlled inference-overhead benchmark. Mobile checks use Chromium viewport emulation; physical iPhone Safari and Firefox remain unverified. No actual model workload was started for testing. GitHub publication remains pending owner instruction.

한국어 요약: 실제 Spark에 개발 패키지를 적용하고 8개 상세창, 실제 측정값, 모바일 2열 배치, 로그인·설정 유지, 복구 후 재적용, 수집 캐시 및 메모리 상한을 확인했습니다. 기존 칩 그림과 모델 서비스는 유지했으며 GitHub에는 배포하지 않았습니다. 그래프 이력은 대시보드 재시작 시 초기화됩니다.
