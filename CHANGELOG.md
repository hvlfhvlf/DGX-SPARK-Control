# 0.3.1 — 2026-11-04

- Measured inference throughput for supported TensorFold/vLLM/Strata endpoints, bounded history and selected LLM details.
- Reviewed discovery/registration of existing user services, editable connections and private model-file inventory.
- Startup status/progress, explicit failed-start retry, Programs with demand-driven CPU/RSS/uptime.
- Optional two-stage password-confirmed power actions, date-grouped searchable/filterable activity and confirmed clear.
- Compact responsive layout, memory usage percentage, retained edit drafts and consistent typography.
- Fix response-body deadlines, stale-session 401 handling, LLM selection request races and stale context metadata.
- Bilingual installation/user guides and privacy-reviewed ARM64 package. Existing private settings, logins and model processes are preserved.

Candidate notes below describe historical development stages, now incorporated into 0.3.1. See docs/releases/0.3.1.md for current validation and limitations.

# 0.3.1~rc10 — request and metadata correctness (local candidate)

Keep the API deadline active through response body consumption. Stale unauthorized replies cannot revoke a newer browser login. Ignore an older inference response after selecting another LLM and immediately fetch the current selection. Clear cached context metadata before refreshing the model endpoint, avoiding an earlier engine run's context limit after a failed lookup. Add failing-before/passing-after regression tests for all four findings. No lifecycle commands or authentication schema changes.

# 0.3.1~rc9 — visual consistency (local candidate)

Remove the selected LLM monogram, use the existing shared interface font in inference headings/units, and left-align activity dates beside disclosure markers. No backend or control changes.

# 0.3.1~rc8 — usability audit fixes (local candidate)

Preserve unsaved input and disclosure/focus during refresh; retain editor drafts on failures and across section saves; readiness-aware app links; compact mobile cards and sticky editing actions; clearer model inventory and package update guidance; activity search/filter/date folding; service-process filtering and low-rate display. No auth/model command changes.

# 0.3.1~rc4 — local candidate

- Add demand-driven TensorFold/vLLM/Strata throughput and active LLM panel.
- Add reviewed web registration/control of existing user services and new profiles.
- Add editable model scan roots and private model file inventory.
- Preserve model processes, authentication and package memory limits. Not published.

# Changelog

## 0.3.1~rc3 (local candidate)
- Remove the header version/LIVE badge; retain version details in Settings and the footer.
- Compact activity row padding and date spacing on desktop and phones without truncating failure guidance.

## 0.3.1~rc2 — local validation candidate

- Date-grouped activity with localized actions/statuses and persistent CLEAR display history.
- Header SVG power button opens restart/shutdown selection; existing two-step password confirmation retained.
- Preserves running operations and newer events when clearing. No GitHub publication.

## 0.3.1~rc1 — local validation candidate

- Real engine startup progress, explicit readiness, failed-start recovery and warnings.
- Read-only Programs tab with demand-driven CPU/RSS/uptime.
- Optional password-confirmed, two-stage Spark power controls.
- No public release or GitHub upload for this candidate.

## 0.3.0 — 2026-11-03

- Publish the validated rc1–rc4 service controls and compact telemetry details. Start/stop/restart registered user services, switch stopped profiles, discover read-only candidates and open configured apps.
- Edit service/model/quantization/inference/serving labels and save shared card order. Mobile cards keep two columns; confirmation has equal-width lime Confirm and red Cancel.
- Eight live detail views retain real data, missing-value semantics and collapsed technical notes. SSD capacity uses composition instead of history.
- Refresh Korean/English install, update and model handoff guides; document privacy boundaries and exclude per-device credentials/addresses/configuration from release files.
- Existing passwords, remembered sessions, registrations, model engines and the 480 MiB dashboard limit are preserved.

## 0.3.0~rc4 — 2026-11-02 · unpublished candidate

- Add authenticated display-label editing and service ordering, persisted on Spark across devices. Only name/model/quantization/inference/serving labels can change; launch bindings and permissions stay local. Stale edits are rejected.
- Compact service cards with two columns on phones, an edit pencil and a collapsed add/replace guide.
- Move telemetry summary notes to the right and remove the separate note row. Tighten all eight metric detail headers and summary spacing.
- Retain rc3 equal-width confirmation/cancellation. GitHub publication remains on hold.

## 0.3.0~rc3 — 2026-11-02 · unpublished candidate

- Give service confirmation dialogs an equal-width, full-row Confirm/Cancel footer, with lime confirmation and red cancellation. Keep two columns on phones and the existing close/focus behavior.
- UI-only follow-up; no service control, registry or authentication changes. GitHub publication remains on hold.

## 0.3.0~rc2 — 2026-11-02 · unpublished candidate

- Add direct application links on service cards and details, configured only in each Spark private registry. Existing authentication and Tailscale routes remain.
- Add per-profile display model name, quantization, inference engine and serving engine, with escaped compact card text and detailed labels. Values come from verified operator configuration, not filename guesses.
- Preserve every rc1 control, telemetry and safety boundary. No GitHub publication.


## 0.3.0~rc1 — 2026-11-02 · unpublished candidate

- Redesign eight live metric details, preserving actual timestamps, missing-data semantics, compact responsive layouts and the original chip artwork.
- Replace SSD history with capacity composition; collapse technical collection details and remove repeated statistics.
- Add private schema-1 service/profile/asset registry, revision-checked local CLI and atomic 0600 storage. Migrate existing model registrations without starting services.
- Add bounded asynchronous systemd-user start/stop/restart, persistent operation status, duplicate/conflict protection and stopped-profile selection.
- Add read-only user-service discovery/registration; separate process status from ComfyUI API/queue and optional OpenAI-compatible API checks.
- Keep logs, prompts, commands, credentials and private registry out of the browser response and distribution. Normalize archive ownership metadata.
- Preserve existing authentication, hardware collection, package setup/tray and 480 MiB combined limit.
- GitHub publication is on hold. See docs/releases/0.3.0~rc1.md for evidence and limits.

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
# 0.3.1~rc5 — local candidate

- Replace the overview memory clock placeholder with used memory / OS-usable memory percentage, to one decimal place.
- Preserve the existing right-aligned reading, gauge, card size and phone two-column layout. Missing or disconnected readings remain unknown.


## 0.3.1~rc6 (local candidate)
- Removed the standalone CONNECTION card action; grouped Display and Connection under EDIT with section drafts and compact two-column navigation. Existing check/review/save and revision guards remain.

## 0.3.1~rc7 (local candidate)
- Aligned equal-width inference/LLM panels to the telemetry grid. Matched headers, compact chart/body spacing, bottom-aligned engine actions and responsive stacked panels.
