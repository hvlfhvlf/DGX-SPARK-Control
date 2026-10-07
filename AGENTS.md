# Continuation contract

Read README.md, docs/ARCHITECTURE.md, docs/MODELS.md, docs/UPDATES.md and the current docs/releases/<VERSION>.md before modifying this project.

## Invariants

1. Keep the installed Spark server below **512,000,000 bytes** for the whole dashboard cgroup. Do not remove the 480 MiB hard limit. Target normal use well below 200 MiB. Measure before claiming low overhead.
2. The server uses one process and Python standard library with on-demand cached collection. An optional GTK desktop tray has no metric polling. Put both in dgx-spark-control.slice, capped at 480 MiB combined. No heavyweight monitoring stack.
3. Never report fixture values as live data. The original public prototype is independent. `web/runtime.js` owns the installed runtime. Unavailable fields are null / `—`, not zero. Reset rate baselines after gaps or counter resets.
4. Keep minimum two-column telemetry on phones, fixed card dimensions, tabular numbers, left main reading/right clock, 0.2s hover, 0.3s detail entry/0.2s exit and reduced-motion support.
5. `DGX_SPARK` is the fresh-install display-name default; changing it does not rename the OS host. Server name is shared, theme/language are browser preferences.
6. No host mutation on GET. Authentication for every private API. Never accept arbitrary shell commands from a browser. Model operations must resolve an explicit local registry and user service.
7. No automatic stopping or replacing an existing LLM to run tests. Use a disposable test service and temporary registry. Preserve installed models, drivers, config and secrets.
8. Before a release update VERSION, CHANGELOG.md and docs/releases/<version>.md. Keep an exact test/validation record, package, checksum, immutable Git tag and GitHub Release aligned.
9. Update the project's Notion release record with the same version, source commit, docs links, evidence and limitations. If Notion is inaccessible, say so; do not call the release documentation complete.
10. Exclude local tokens, real paths/registries, logs, benchmark prompts, SSH configuration and unrelated media from source and releases.
11. Device logins have no fixed expiry, by explicit owner preference. Keep them across browser close, server restart and update; revoke on logout/password reset. Persist bounded session hashes, never passwords or raw session tokens. Local OS account access permits password recovery without knowing the old password.
12. Never hardcode 128 GB, GB10 or 20 cores in the installed UI. Hardware identity comes from the authenticated API; distinguish installed firmware RAM from OS-usable MemTotal. Missing firmware must not be rounded into a guessed marketed capacity.
13. Render decorative arrows with inline SVG, not Unicode arrows that can become emoji on iOS. Keep icon geometry, currentColor, accessibility and sizing consistent. Keep docs/GUIDE.ko.md and docs/GUIDE.en.md aligned when user-facing behavior changes.

## Verification

On Linux: `python3 -m unittest discover -s tests -v`; syntax-check all web JavaScript; run `bash -n install.sh update.sh scripts/rollback.sh`; inspect real browser desktop and 320/390 px behavior. Test install, restart, persisted rename, update and rollback on Spark. Check cgroup memory.max, memory.current, memory.peak and memory.events; idle collection count must not increase. Do not claim end-to-end inference overhead without a controlled workload comparison.

Prefer targeted modules over prototype-wide rewrites. Subsequent engine adapters should expose capability flags and explicit readiness/metrics; only supported capabilities are shown. Do not infer model context/quantization from a filename.
