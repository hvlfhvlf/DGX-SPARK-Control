# Changelog

## 0.2.1 — 2026-10-09

- Use bundled SUIT 2.0.5 Regular/SemiBold/Bold WOFF2 for Korean web UI, including labels, navigation, settings and detail dialogs.
- Serve fonts from the Spark itself, without external font/CDN requests. Keep the upstream SIL OFL license and exact source attribution.
- Preserve the Rajdhani numeric/English display style, the English Chakra Petch UI, and system-font fallbacks. Refresh the stylesheet cache key.
- Keep the native GTK setup/tray typography unchanged; this release updates the browser dashboard only.

## 0.2.0 — 2026-10-08

- Add an Ubuntu ARM64 `.deb`, application-menu setup launcher, and four-step Korean/English GTK wizard.
- Detect existing passwords and preserve remembered device sessions during archive-to-package migration; require a confirmed password before activating fresh installs.
- Add read-only JSON checks, interactive CLI setup and existing-password-only noninteractive activation for SSH/LLM workflows.
- Keep code owned by dpkg and private user data outside it. Refresh active managed users after package updates, retain old archive code and back up units/settings before migration.
- Add tray actions for copying the detected Tailscale address, reopening setup and opening GitHub Releases. No additional polling or resident installer.
- Publish parallel Korean/English quick-start and user guides, with explicit Tailscale, permissions, startup, recovery, update and removal instructions.
- Keep other-platform expansion on hold; preserve the 480 MiB server/tray cap and existing model services.

## 0.1.2 — 2026-10-08

- Replace diagonal text arrows with inline SVG in the brand, schematic, telemetry cards and shared UI actions, preventing platform emoji substitution while retaining the existing visual style.
- Scope schematic SVG sizing to the illustration, keeping inline label icons at text size on phones.
- Publish separate Korean and English installation/usage/recovery/update guides, linked from the repository README and included in the release package.
- Keep the existing Tailscale address, display name, authentication policy, model services and server dependencies unchanged.

## 0.1.1 — 2026-10-08

- Replace fixed hardware labels with detected GPU, architecture, CPU count and installed/OS RAM capacity. Validate 64/128/256 GiB fixtures.
- Choose a password during interactive installation; PBKDF2-SHA256, local reset without the old password, no plaintext persistence.
- Keep device sessions without a fixed expiry, including server restart/update and browser close. Logout/password reset revokes access. At most 32 session hashes are persisted.
- Optional Spark desktop tray: open dashboard, rename, password recovery, start/restart and status. Combined server/tray memory cap remains below 512 MB.
- SSD detail shows root filesystem scope, exact used/available/reserved bytes and the distinct Linux df percentage.

## 0.1.0 — 2026-10-08

- First installable Spark-hosted runtime: one Python process, no external Python dependencies.
- Cached on-demand NVML/Linux telemetry, eight live cards and real sample history.
- Fresh-install name `DGX_SPARK`; Settings persists the shared name on the Spark.
- Token-protected API, explicit user-service start/stop, bounded model candidate discovery.
- Versioned installer, checksum-verified update path, previous-code rollback and config backups.
- Whole dashboard service limit 480 MiB (<512 MB), no swap, bounded workers/history.
- Korean/English runtime, existing responsive visual language and modal transitions preserved.
- LLM handoff, architecture, model integration, installation and release documentation.

Limits: request queue, inference throughput and engine readiness adapters are future work; long-term persistent telemetry is disabled. Consult docs/releases/0.1.0.md for validation status.
