# DGX-SPARK-Control user guide — English

**0.3.4** · [한국어](GUIDE.ko.md) · [Easy installation](QUICKSTART.en.md)

## Metric details

Click any of the eight overview cards to open its own detail dialog: key readings, a 1-minute / 5-minute / 1-hour history, then metric-specific information. Phones retain two columns of key readings. SSD capacity has no time chart: it shows used/available/percentage/total, a composition bar and the mount point. Expand **Capacity details & calculation** for reserved space and df accounting. Memory shows used and available capacity; CPU shows per-core load; temperature lists reported sensors; network and disk I/O show both directions. SSD capacity covers the root filesystem; power covers the GPU.

The seven metrics other than SSD capacity have charts with time and units. Memory uses the reported capacity as its ceiling; CPU/GPU utilization uses 0–100%. Other axes never shrink while the same dialog/range is open. Average and peak include valid collected samples only; missing intervals remain gaps. Rates use MB/s; headline readings at or above 1,000 MB/s switch to GB/s.

A dash means unsupported, unavailable or warming up. Disconnections retain the last readings and their original timestamp. Uncollected values such as memory clocks, whole-system power or IOPS are not invented. Expand **Measurement notes & sources** for included interfaces/devices, sensor identifiers, clock availability, units and calculation details. These technical notes are collapsed by default; live readings, per-core load, sensor temperatures, capacity composition and clock-limit events remain visible. Repeated architecture and graph statistics are omitted. Close using the button, Escape or backdrop. Updates preserve range selection, scroll position and expanded notes.


## Installation and access

Follow [Easy installation](QUICKSTART.en.md), install the `.deb`, and open **DGX-SPARK-Control Setup** from Applications. Choose Korean or English, save your display name and password, and start the server. Leave both password fields empty to keep an existing password.

On Spark use `http://127.0.0.1:8767`; other devices use its Tailscale HTTPS address. **Copy connection address** in the tray prefers the detected HTTPS route. Without that route, it copies the local address and explains the limitation.

## Login and recovery

The same browser at the same address stays signed in without a fixed expiry, including restarts and updates. Logout, password reset or browser data removal ends the login. Another browser, address or private window may require a new login. Up to 32 sessions are kept; a 33rd removes the oldest issued session.

If you forget the password, use **Reset password** in the local Spark tray. The previous password is not required. For terminal recovery on a package installation:

```bash
python3 /usr/lib/dgx-spark-control/scripts/set-password.py
systemctl --user restart dgx-spark-control
```

Plaintext passwords are never saved. Do not share password hashes, maintenance tokens or session files, or upload them to GitHub.

## Live measurements

| Card | Meaning |
|---|---|
| GPU | Utilization and supported SM clock |
| CPU | Aggregate/per-core usage and readable clocks |
| Unified memory | OS used/total memory and used percentage |
| SSD | Root `/` filesystem used/total/user-available/reserved-free space |
| GPU temperature | Temperature provided by the driver |
| GPU power | GPU sensor reading, not whole-system wall power |
| Network | Physical interface receive/send MB/s, not isolated internet traffic |
| Disk I/O | Physical disk read/write MB/s |

Click a card for real history and details. Unsupported or not-yet-ready readings display `—`. Installed RAM uses readable firmware capacity; otherwise the OS total is explicitly labeled. Capacity is never guessed as 64/128 GB. The SSD card's used ratio may differ from `df` due to reserved space.

## Settings and tray

The Spark display name is shared across devices. It does not change the OS hostname or Tailscale URL. Web language and personalization are browser preferences; the setup language is saved locally.

Tray actions include open dashboard, copy address, setup, check for updates, rename, reset password, start/restart server, status and close. Checking for updates opens GitHub without installing automatically. Restarting the dashboard does not restart models. Closing the tray leaves the server running.

## Model management

Existing user systemd services must be registered in the private `services.json` registry before control is allowed. Legacy `config.json.models` is migrated once. Model discovery lists file candidates under configured paths. It does not download, delete, register or switch models automatically. Service `active` is different from inference readiness.

Read [Model integration](MODELS.md), back up configuration and add only the intended models. The dashboard displays measured inference tok/s and engine-local request counts for supported engines. TTFT and global queues are not provided.

## Updates, resources and troubleshooting

Update a `.deb` installation by installing the newer `.deb`. Do not mix package and legacy script update methods. [Updates, recovery and migration](UPDATES.md).

```bash
systemctl --user status dgx-spark-control
journalctl --user -u dgx-spark-control -n 50
tailscale serve status
systemctl --user show dgx-spark-control.slice -p MemoryCurrent -p MemoryPeak -p MemoryMax
```

The server and tray share a 480 MiB limit with no swap. Browsers, models, setup and Tailscale are separate. There is no telemetry collection without client requests. Long-running inference impact requires a separate benchmark.

For another LLM continuing development, read [AGENTS.md](../AGENTS.md), [Architecture](ARCHITECTURE.md), [Models](MODELS.md) and [Updates](UPDATES.md). Keep secrets out of public materials. [This release's validation](releases/0.3.1.md).

## Korean web font / iPhone

The Korean web UI uses SUIT 2.0.5. Regular (400), SemiBold (600) and Bold (700) WOFF2 files are served by your Spark, with no iPhone font installation or external font CDN required. Rajdhani remains the numeric/English display font and Chakra Petch remains the English UI font. System Korean fonts appear while the web font loads or if loading fails.

Safari supports WOFF2 web fonts, although glyph rendering may differ slightly between Windows and iPhone. [WebKit font support](https://webkit.org/blog/6643/improved-font-loading/). Refresh the page after updating if the old typeface remains. Native GTK setup/tray typography is outside this change.


## Service controls and model display

Models provides start/stop/restart and operation results. Select launch profiles in Details while stopped. Add service discovers existing user services and enables control after connection review; the local registry CLI is also retained. ComfyUI running/pending counts and API readiness are separate from process state. Hermes and engines without configured probes show process status only. Models are never automatically installed or deleted. [Registration and replacement](MODELS.md).


Cards with a configured application address provide **OPEN APP**; the application retains its own login. Model cards use the full model name as their title, quantization directly beneath it, and smaller inference/serving engine labels. These are verified launch-profile settings, not evidence that a stopped model is loaded. Unverified quantization displays "Not verified".

Service confirmation dialogs have equal-width Confirm (lime) and Cancel (red) buttons. Cancel only dismisses the dialog; it does not change the service.


Use the pencil on a model card to edit the service name, full model name, quantization, inference engine and serving engine labels. Use Order, move cards up/down, then Save. Labels and order are stored on Spark and shared across devices; commands, ports, permissions and model files are unchanged. Reopen the editor if another device has already saved changes. Phone cards use two columns and the add/replace guide is collapsed. Metric detail notes (Current/Selected range) sit on the right.

See [privacy and data flow](PRIVACY.md). Open App opens a configured address; configure the engine application’s Tailscale access separately.


## Operations

- Card-top status: amber while loading, lime for API readiness, red for failure. Opt-in TensorFold profiles report actual loaded layers. 100% weights is not server readiness. Engines without progress report a phase and elapsed time; process-only services are labelled separately.
- Start after failure checks for residual processes, clears the selected unit's failed/start-limit state and attempts one start. A failed attempt opens an actionable warning. It never bypasses memory checks, changes engine settings or stops other models.
- Programs replaces Jobs: account/all scope, name/PID search, CPU/RSS/uptime sorting. Shared 5-second cache; collected only while viewing the tab. CPU is normalized to whole-host capacity. RSS includes shared pages and must not be summed as actual physical memory usage. Command lines and environments are not collected.
- Header power icon → Restart/Shut down requires an interruption warning followed by password re-entry and an explicit final action. Confirmations expire after 60 seconds, are session/action-bound and single-use. An incorrect password does not log out your device. Powering on after shutdown requires local access or a separately configured wake mechanism.

After package installation, a local administrator can opt in to the fixed power helper. This command never executes a power action. Other users' sessions and shutdown blockers prevent execution.

```bash
sudo python3 /usr/lib/dgx-spark-control/packaging/configure-power.py --user "$(id -un)"
# Add --disable to remove this permission.
```

For TensorFold progress, set `"startup_observer": "tensorfold"` in the local launch profile and validate/apply with `services check/apply`. Only fixed counters/error codes from the current invocation are projected. A configured API probe also has to succeed. Raw logs, prompts and credentials stay on Spark.


### Activity and header power controls
Activity is grouped by calendar date in the device time zone, newest first. CLEAR asks for confirmation and clears the reviewed finished display history across devices, preserving ongoing/new events, service recovery records and system logs. The cleared view persists across server restarts. The header power icon offers restart/shutdown choices before the existing warning and password-confirmation steps. The duplicate Settings power section is removed; use the header icon.


## Compact status display
The header version/LIVE badge is removed. Version details remain in Settings and the footer. Activity rows and date spacing are denser on desktop and phones; failure guidance and clear confirmation remain available.


## Inference and web registration
Overview shows aggregate output/input token throughput on the left and the selected LLM service on the right. TensorFold, vLLM and Strata adapters expose only available metrics. Input is token-counter delta per elapsed second, not prefill compute speed. Output uses an engine window or counter delta; inspect Measurement notes for its source. Completed-request counters may be bursty. No prompts or completions are collected.

History is collected on demand every 5 seconds while Overview is open, with 5m/30m/1h views. Up to four streams of 720 samples are held in memory and cleared on restart. Missing samples remain gaps. Zero is valid for an idle engine.

Models → Add service → select an existing user systemd service → choose adapter, local API port and optional app URL → enable control if desired → Check connection → Save. Saving does not start it. Stopped services can be registered with unverified API readiness, then started. The API is local to this Spark: if loopback refuses the connection, only an OS-verified local IPv4 listener may be used. No arbitrary shell commands or remote probe URLs are accepted. Connection settings edit observation and control settings; they do not change the engine command.

An additional existing service can be added as a profile to an existing card. Stop before selecting a different profile, then start. Model files lets you save scan roots, discover candidates and register filenames/display names in a private inventory. Inventory registration does not create launch commands. Engine/weight download or deletion, direct Docker/system-service control and generating engine launch templates from files remain outside this release.

## Memory card percentage
The right reading is used memory / OS-usable total × 100, to one decimal place. It uses the same basis as the GiB reading and gauge, rather than installed capacity. Missing or disconnected data displays —%.


## Unified service editor
The separate CONNECTION card button is removed. Open the pencil (EDIT), then Display or Connection to manage labels or API port, app URL and control permission. Switching sections retains drafts; saving applies only to the current section. Connections still require check, review and save. Cancel or close does not save.

## Inference panel alignment
Desktop throughput and active-LLM panels have equal widths aligned to the telemetry columns, matching headers and compact chart spacing. Engine actions sit at the bottom. Narrow screens stack these panels; the eight telemetry cards retain at least two columns.

## Editing, filtering and recovery
Change the Spark name using the input and Save button. Automatic updates preserve the draft while Settings stays open. Leaving Settings for another dashboard tab or reloading the page discards unsaved name edits and restores the last saved name. There is no Cancel or Undo button. Service editor sections save separately; when another section has changes it remains open. Service editor save failures retain the draft; closing asks before discarding changes. Browser reload may show a warning for unsaved service edits. Drafts are not permanently stored.
Stopped apps show Start to open; unready APIs show App not ready; process-only apps show Open App. Details explains: Process running confirmed · Connection status not checked. This is not a guarantee of successful app authentication.
Model files are inventory, not generated launch configurations. Connect an existing user service already configured for the model. Docker/terminal setup and installation remain local Spark tasks.
Activity supports search, failed/interrupted filtering and date folding. Clear includes completed entries outside the filter, across devices. Service-process filtering excludes common desktop/system groups; it is not exclusively a registered-model list.
Package installations update through the new .deb with apt, never archive update scripts.

## Status and control guidance (0.3.4)

- **API responding** means the current API answered; it does not guarantee successful generation or performance. **Last action** describes a historical control request separately from current health.
- Process-only services use **OPEN APP** and explain **Process running confirmed · Connection status not checked** in Details. Unreachable, unknown and disconnected states are not presented as ready.
- If the profile/settings change or the connection is lost after opening a confirmation, controls are disabled. Close and review again against fresh state. Retrying a failed Stop retries Stop.
- Add service registers its connection and optional control permission; it does not start it. Registering a model file does not create a launch profile.
- **Dashboard OS account** in Programs means the OS account running the dashboard on Spark, not the user on the visiting device.
- Clear activity applies to finished successful, failed and interrupted entries. The Spark name is shared; appearance and language belong to the current browser.


### Layout density and header controls
On phones, model cards no longer reserve empty metadata/action rows. Service details use compact label/value rows, and all eight metric dialogs use tighter summary, chart and explanatory spacing. Controls and measured data are unchanged; desktop geometry is preserved. Expand the existing notes for longer explanations.
Desktop spacing is unchanged. At widths of 600px and below, Comfortable uses a denser phone layout and Compact reduces spacing further. Reading font sizes and two telemetry columns are preserved; cards have fixed heights of 144px and 132px respectively. At 390px, the eight-card grids measure 600px and 546px. Repeated Live sensor labels are hidden on phones while clocks, percentages, total capacities and graphs remain. Headings and inference panels also use less whitespace; primary action targets remain at least 44px. The overview artwork has its own collapse button. Density is saved in this browser. Language and power buttons both measure 68×44px on desktop and 44×44px on phones. The two-stage power warning and password confirmation remain.

## Color presets and black / white modes

Use the sun / moon icon beside Language and System power to switch modes. Black is the default. Settings → Accent color shows Acid lime, Lavender and Ice blue with color chips. The selection applies to controls, charts and chip artwork; warning and failure colors retain their meaning. White mode uses darker accent text and graph lines for legibility. Appearance is saved per browser and restored on reload; it does not change other devices.

## DeepSeek Harness connection (0.3.4)

Register the existing `deepseek-harness.service` with the process adapter, explicit control permission and its HTTPS app address. **Open App** obtains the current Harness authentication URL through the signed-in dashboard and opens a new tab. Allow pop-ups for this dashboard if blocked. Never paste a token into the app URL field. The current integration supports the local default Harness layout and port 3080.

Harness process state and the connected LLM's readiness are separate. Its configured inference server must also be running to answer requests. Harness start/stop controls only that app; it does not automatically start or stop the model. The dashboard does not collect conversations or workspace files.


## App updates (0.3.4)

Model Bay → Details shows the installed app version. **Check for updates** contacts the official source; when a compatible candidate is available, it becomes **Update**. Stop the app first. Confirm **Back up & update** to create a private snapshot, install and perform basic validation. A failure attempts restoration; a recovery warning means local attention is required. Start the app manually afterwards and test its normal workflow. Running apps are never automatically stopped. Unsupported profiles show unavailable instead of a guessed version.

The dashboard does not update model weights, CUDA/drivers or ComfyUI custom nodes. See [local update setup and recovery](SERVICE-UPDATES.md). Updates may require temporary disk space and up to 2 GiB installer memory outside the monitoring process.

### Application backup storage
Checking for updates creates no backups. Applying an update does. Successful validation retains one managed recovery backup per service. Old and new copies coexist temporarily, so extra free space is required. Failed/review-required recovery material is retained and further updates are blocked until local review. Model/media directories and ComfyUI custom nodes remain in place.

### Start services at boot (0.3.4)
The boot control uses the same rectangular switch as Settings. The colored square on the right means ON; the left position means OFF. A disabled dash means the state is unavailable; saving temporarily locks the control.

Model Bay → Details → **Start when Spark boots**. ON/OFF applies to the selected launch profile and persists on Spark for all dashboard clients. It does not start or stop a service now. OFF does not prevent manual/dependency starts. The actual service setting is read on opening Details; no periodic scanning is added.
User lingering must be enabled on Spark for startup before login. Unsupported, masked/static, or compound Install configurations require local setup. Only registered controllable user services targeting default.target are editable. Turn off conflicting profiles first and turn off the current profile before replacing/removing it. Dependencies and model memory capacity still need appropriate local configuration; enabling startup does not guarantee the inference API becomes ready.


## Connection reliability (0.3.4)

Delayed updates and disconnected nodes are separate states. Controls pause during telemetry delay. History/activity failures affect only their section; polling recovers automatically. History loads only for visible graphs, using incremental samples after the first read. Restarting the server resets the cursor. Hidden tabs pause regular polling.


Closed service dialogs no longer keep status requests alive. App-update status pauses in a hidden tab and resumes when returning to visible Details. Closing Details does not cancel an update already accepted by Spark; reopen Details to inspect it.

Before the first reading arrives, the overview shows Connecting; this is not a disconnected node.

