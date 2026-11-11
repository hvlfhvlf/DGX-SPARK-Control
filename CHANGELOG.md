# 0.3.4 — 2026-11-11

- Publish the Settings-style rectangular boot-autostart switch in service Details.
- Retain a 44px touch target, keyboard semantics, theme colors, saving lock and explicit unavailable state. No backend, authentication, schema or lifecycle changes.
- Align Korean/English installation, user and LLM guides and release packages.

Validation and limitations: [0.3.4 release record](docs/releases/0.3.4.md). The candidate below is historical and is included in this stable release.

# 0.3.4~rc1 — local UI candidate, 2026-11-06

- Match the service boot-autostart control to the rectangular Settings switch. Keep a 44px touch target, keyboard switching, theme colors, saving lock and explicit unavailable state. No API or lifecycle changes. Private at the time; incorporated into 0.3.4.

# 0.3.3 — 2026-11-06

- Publish the tested rc1–rc6 runtime: secure on-demand Harness app opening and correct start-after-stop port checks.
- Add opt-in official Harness/Hermes/ComfyUI update checks, version display, stopped-app guards, private backups and failure recovery in service Details.
- Add per-profile boot autostart controls with actual user-systemd state, conflict/revision checks and no immediate lifecycle change.
- Reduce history/activity requests, bound multi-client concurrency and distinguish initial connection, delayed updates and disconnected nodes.
- Stop hidden-dialog polling and ignore stale update responses; preserve settings, remembered logins, model processes and the 480 MiB monitoring cap.
- Align Korean/English installation, user and LLM guides; document temporary updater resources and recovery limits.

Validation and limitations: [0.3.3 release record](docs/releases/0.3.3.md). Candidate notes below are historical development records, now incorporated into 0.3.3.

# 0.3.3~rc6 — private candidate, 2026-11-06

- Stop service polling triggered solely by hidden Details/confirmation content. Visible service pages and pending operations still refresh.
- Pause app-update status polling when Details closes or the tab is hidden; resume visible Details when returning.
- Ignore late update-check failures after closing/replacing the dialog, avoiding unexpected modal reopening.
- Show initial telemetry/inference loading as Connecting instead of failure; unknown CPU core count is unavailable, not zero.
- No model lifecycle changes, new daemon, schema migration or GitHub publication.

# 0.3.3~rc5 — private candidate, 2026-11-06

- Separate telemetry connection state from optional history/activity and rendering errors. Show delayed updates before repeated failure; pause controls and recover automatically.
- Fetch history only for visible graphs/details, merge incremental samples with a restart epoch, cache settings for 60 seconds and activity only in its tab.
- Bound each browser to 3 concurrent requests and 24 queued requests; jitter poll cycles and retry GET overload once, never replay writes. Keep 8 server workers; bounded admission returns HTTP 503/Retry-After.
- Preserve authentication, configuration, running models and the 480 MiB cap. No GitHub publication.

# 0.3.3~rc2 — local candidate, 2026-11-05

## 0.3.3~rc4 (private candidate)
- Service Details: per-profile boot autostart ON/OFF reads and changes actual user-systemd settings, without starting/stopping the current process.
- Registered units only; authentication, Origin, revision and maintenance lock checks. Detect linger, unsupported installs and conflicting boot profiles; disable autostart before rebinding enabled profiles.
- No recurring poll, extra daemon, credentials or public release.

## 0.3.3~rc3 — local candidate

- Details: installed application version, explicit official update check and reviewed update action; compact responsive layout.
- Opt-in Harness, Hermes and ComfyUI adapters; stopped-process and unit guards, private full environment/state backups, automatic failure recovery.
- A bounded transient updater runs outside the dashboard memory slice; services remain stopped. No GitHub publication.

- Fix immediate start after HTTP service stop: ignore leftover TIME_WAIT sockets in port preflight while still refusing an active listener. Add a real-loopback regression. GitHub publication remains on hold.

# 0.3.3~rc1 — local candidate, 2026-11-05

- Add authenticated, on-demand DeepSeek Harness app opening for an explicitly controllable `deepseek-harness.service` registration. Read only a bounded local startup log; require matching configured HTTPS origin and a successful local authentication exchange. Never persist or list the launch token.
- Preserve process-only status, existing model services, authentication and registry schema. No engine installation or automatic inference request. Not published to GitHub.

# 0.3.2 — 2026-11-05

- Publish rc1/rc2 state and control safety fixes: current versus historical health, invocation/revision-aware readiness, reviewed-action binding, failed-stop retry and stale-session response rejection.
- Add black/white modes, semantic accent presets with color chips, and documented extension-safe theme variables.
- Compact phone telemetry, Model Bay, service/edit dialogs and eight metric details while retaining desktop geometry and touch targets; fix narrow CPU percentage overflow.
- Simplify name editing, remove duplicate Settings power controls and align header buttons. Clarify registration, app links, data scope and control states.
- Add Korean/English LLM playbooks with copyable installation, registration, display editing and model replacement requests. Preserve private settings, device logins and model processes.

Validation and remaining limitations: [0.3.2 release record](docs/releases/0.3.2.md). Earlier candidate notes below are historical, not the current publication status.

# UI development notes — incorporated into 0.3.2

- Add phone-only spacing overrides at 600px and below, leaving desktop geometry unchanged. Fixed two-column telemetry cards are 144px in Comfortable and 132px in Compact; remove repetitive source labels on phones while retaining readings, clocks, capacities and graphs.
- Reduce phone heading, inference, service and settings spacing without reducing telemetry reading fonts or 44px action targets.
- Compact phone model cards, service/edit dialogs and all eight metric dialogs. Remove empty reserved fields/action rows, retain 44px controls, and prevent 100.0% per-core readings from overflowing narrow phone cells. Desktop model/detail geometry remains unchanged.

- Centralize surface, accent, chart, artwork, hover and semantic status colors. Remove fixed green values from component styles.
- Add color-chip preset buttons and a sun/moon header toggle with browser-local persistence and pre-paint restoration.
- White mode uses darker text/chart accents and bright filled controls with paired foregrounds. Secondary chart colors stay distinct from the selected accent.
- Keep aligned 44px header controls, two-column phone telemetry, existing fonts and chip geometry.
- Add palette contrast, storage compatibility, preference interaction and component color regression tests; document the theme contract in `docs/THEMING.md`.
- These changes were first validated as local static assets and are included in 0.3.2.

# 0.3.2~rc2 — local usability and state audit, not published

- Separate current API health from historical request failures; label latest action explicitly. Unknown/offline/unreachable states no longer look ready to open.
- Invalidate cached API readiness when a systemd invocation or registry revision changes.
- Bind action confirmation to the reviewed profile/revision; disable stale/offline controls and keep service Details refreshed outside Models.
- Retry failed Stop as Stop; reject late successful private responses after a session change.
- Clarify control permission, registration, shared/browser preferences, process scope and clearing finished activity. Keep registered model-file buttons disabled.
- Initial loading displays Connecting instead of a false Connection lost warning; version is unknown until loaded.
- Includes rc1 app-link wording. Public release remains 0.3.1. No GitHub publication.

# 0.3.2~rc1 — local candidate, not published

Use Open App for process-only application links. Show Process running confirmed / Connection status not checked in service Details while running, updating the note with live state. Preserve existing loading/stopped/unreachable access restrictions. No backend, authentication or lifecycle changes.

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
