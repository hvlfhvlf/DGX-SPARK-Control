# Ask an LLM to install and manage Model Bay

**0.3.2 · DGX Spark / Ubuntu ARM64** · [한국어](LLM-GUIDE.ko.md)

Give this document to the agent doing the work. A coding agent with authorized Spark terminal/SSH access can execute installation and registration; a chat-only LLM can only explain them. The dashboard does not run a resident LLM agent.

## Choose the right operation

| Goal | Workflow | What it does not do |
|---|---|---|
| Install/update the dashboard | Official `.deb`, then setup | Install or replace models, CUDA or drivers |
| Add an installed inference server/app | Model Bay → Add service → existing user service | Download an engine or automatically start it |
| Rename service/model/quantization/engines | Pencil → Display → Save | Change the executable or loaded model |
| Edit observed API port/app URL/control permission | Pencil → Connection → Check → Save | Reconfigure the engine's own listening port |
| Reorder cards | Order → move → Save | Change running state |
| Switch the actual model | Add a verified profile → Stop → select profile in Details → Start | Automatic rollback or weight deletion |
| Find/register model files | Model files → explicit scan roots → register inventory | Generate an executable service from weights |
| Install an engine/weights | Separate local installation, then a user service | A dashboard installation wizard is not shipped |

A **service** is a card, a **profile** binds a launch, and **model files** are an inventory. More files do not automatically mean more servers. Adding a ComfyUI checkpoint normally needs no extra card. Hermes provider configuration is separate from registering its gateway service.

## 1. Copyable installation request

```text
Install DGX-SPARK-Control on this Spark.
Repository: https://github.com/hvlfhvlf/DGX-SPARK-Control
Read docs/LLM-GUIDE.en.md, AGENTS.md, docs/QUICKSTART.en.md,
docs/UPDATES.md and the selected release notes first.
Check OS/architecture and any existing package/archive installation.
Download the official ARM64 .deb and SHA256SUMS; verify before installing.
Preserve settings, password, remembered logins, models, drivers and Tailscale.
I will enter the initial password directly in setup or the interactive terminal.
Verify access, authentication, auto-start configuration and memory limits.
Distinguish checks actually performed from checks still outstanding.
Do not interrupt running models or enable public access/Funnel.
```

Agent procedure:

1. Inspect OS, `uname -m`, and package/archive ownership (for example `dpkg-query -W dgx-spark-control`). A not-installed result is an expected branch. Do not mix package and archive update paths.
2. Download the `.deb` and `SHA256SUMS` from the [official release](https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/tag/v0.3.2) into the same private working directory. Match the selected version and exact artifact name.
3. Run these in the download directory. Confirm that the intended `.deb` reports **OK** before installing.

```bash
sha256sum --ignore-missing --check SHA256SUMS
sudo apt install ./dgx-spark-control_0.3.2_arm64.deb
dgx-spark-control setup --check
dgx-spark-control setup --cli --lang en
```

4. Run setup as the normal Spark user, not root. `dgx-spark-control setup` opens the GUI. Let the owner enter a new password interactively; do not put it in chat, command arguments, scripts or environment variables. `setup --non-interactive` requires an existing password.
5. Package-manager success and a healthy runtime are separate checks. Inspect `setup --check`, `systemctl --user is-active dgx-spark-control.service`, `is-enabled`, and authenticated browser access. Check user-service/linger configuration before claiming boot auto-start; distinguish configuration checks from an actual reboot test.
6. Local Spark access is `http://127.0.0.1:8767`; other devices need the detected Tailscale HTTPS address. An app link is separate from dashboard access. Change Serve/access policies only within the user's requested scope and preserve existing routes.
7. Keep the combined dashboard/tray `MemoryMax=503316480` and `MemorySwapMax=0`. Report observed memory, not an unmeasured inference performance claim.

Updates install a new `.deb` and repeat validation. Dashboard/tray may restart; this is not an instruction to restart model services. Leave both password fields blank to preserve an existing password in setup. Read [recovery instructions](UPDATES.md) and retain a known-good package before updating.

## 2. Add an installed service

```text
Add the already-installed <service/engine> to Model Bay on this Spark.
Read docs/LLM-GUIDE.en.md and docs/MODELS.md; inspect existing registrations.
Preserve working services, weights, drivers and all other cards.
Verify the user systemd unit, local API port and browser-reachable app URL
separately. Choose a supported adapter and leave unknown metadata unavailable.
Use Add service or the revision-checked services CLI.
Grant control only for the service I requested. Register without starting it.
Explain what was registered and what still needs separate installation/setup.
```

Prefer **Add service → existing user service → adapter/local API port/app URL → control permission → Check connection → Save**. Discovery lists user systemd candidates, not every process/port/file on the machine. Stopped services can be registered without confirmed API readiness. Starting is a separate action.

The supported manager is `systemd-user`. Direct terminal-process, Docker and system-service management are not implemented. If a user unit is needed, verify the existing launch, working directory, private environment file and stop behavior first. Do not duplicate a running process or overwrite a working unit. Do not place models inside the dashboard cgroup.

`probe.origin` observes `http://127.0.0.1:PORT` on Spark. `open_url` is a browser-reachable app URL and may differ. Never add API keys to URLs. Engine secret references are not shipped; use process-only observation if authenticated probes are unsupported. A successful `/v1/models` response is not proof of successful inference.

## 3. Edit labels versus replace the actual model

Display-only request:

```text
Change display metadata only for <card> in Model Bay:
service=<value>, full model name=<value>, quantization=<verified value>,
inference engine=<value>, serving engine=<value>. Leave unknown values blank.
Save under Pencil → Display, then order cards as <desired order>.
Do not change profiles, units, ports, model files or running state.
Verify persistence after refresh and returning to the page.
```

Actual new-model/profile request:

```text
Add a <new model/engine> execution profile under <service card>.
Preserve the current profile and files; use a new profile ID.
Inspect existing installation, exact weights/quantization, ARM64/GB10 support,
memory, disk, ports and running workloads first.
If downloads are needed, explain source/revision/size/license and launch changes.
Merge into the current registry, validate and apply with its expected revision.
For this task register only; do not stop, select or start a profile yet.
Explain how to recover to the previous profile and list unverified assumptions.
```

To authorize a switch too, replace the final two lines with: “Stop the specified service, select the new profile and start it without interrupting other workloads. Verify readiness and a small inference request.” Follow the scope of the user's actual request; do not repeatedly ask for already-authorized steps. Report process state, API readiness, successful generation and performance separately.

## 4. Advanced local registry workflow

Read [Models](MODELS.md), [service handoff](development/SERVICE-HANDOFF.en.md) and the [generic example](development/SERVICE-REGISTRY.example.json) for dependencies, timeouts and profiles. Never overwrite the entire live registry with the example.

```bash
umask 077
dgx-spark-control services export > ~/.local/share/dgx-spark-control/services-edit.json
# Back up this private local file; merge only the intended changes.
dgx-spark-control services check --file ~/.local/share/dgx-spark-control/services-edit.json
dgx-spark-control services apply --file ~/.local/share/dgx-spark-control/services-edit.json --expected-revision N
```

- Replace `N` with the actual exported revision. Inspect `missing_units` as well as schema validation. Export initializes an absent registry; it is not a pure pre-install check.
- On revision conflict, export again and merge; do not force overwrite. Apply is atomic and does not start services.
- Do not rebind a running profile. On failure inspect actual state, the sanitized failure reason, ports and available memory. Do not create endless restart/reset-failed loops or kill unrelated processes.
- Keep registry contents, credentials, personal addresses, command arguments and raw logs out of chat, repositories and issues. Report sanitized findings only.

## Completion report

```text
Installed/registered version and source:
Changed cards/profiles/settings:
Existing settings/logins/models preserved:
Process state / API readiness / generation test: verified or not performed, separately
Browser reconnection/mobile check:
Recovery steps and private backup location: local handoff, not public posting
Remaining limitations/unsupported features:
GitHub publication: only if requested
```

When new code is necessary, read [AGENTS.md](../AGENTS.md) and [Architecture](ARCHITECTURE.md), then extend adapters with explicit capabilities. Follow [THEMING.md](THEMING.md) for UI additions. Registering one model does not require rewriting the dashboard.
