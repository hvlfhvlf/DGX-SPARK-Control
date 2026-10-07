# DGX-SPARK-Control user guide — English

Version **0.1.2** · [한국어 가이드](GUIDE.ko.md) · [Release downloads](https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/tag/v0.1.2)

A lightweight web dashboard running on your Spark. View real hardware telemetry and start or stop explicitly registered model services from a browser. The default display name is `DGX_SPARK`.

## 1. Requirements

- Validated target: NVIDIA DGX Spark, Ubuntu 24.04, ARM64, Python 3.12 or newer, user systemd and cgroup v2.
- GPU readings require an NVIDIA driver. The installer does not install or replace models, CUDA, drivers or Tailscale.
- The web server uses Python's standard library. No pip, npm, Docker, database server or LLM agent is required.
- Remote clients and the Spark must join the same Tailscale network with access permitted by its policy.

## 2. Install on Spark

Run these commands in a Spark terminal as your **normal user**, not with `sudo bash install.sh`. They create a fresh working directory.

```bash
mkdir -p ~/Downloads
install_dir=$(mktemp -d "$HOME/Downloads/dgx-spark-control-0.1.2-XXXXXX")
cd "$install_dir"
curl -fLO https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/download/v0.1.2/DGX-SPARK-Control-0.1.2.tar.gz
curl -fLO https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/download/v0.1.2/SHA256SUMS
sha256sum -c SHA256SUMS
```

Continue only if checksum verification reports `OK`.

```bash
mkdir app
tar -xzf DGX-SPARK-Control-0.1.2.tar.gz -C app
cd app
bash install.sh
```

The first interactive installation asks you to enter your chosen password twice. Only a salt and PBKDF2 hash are saved. Non-interactive installations retain local maintenance-token access until you set a password. Installation finishes with an authenticated health check.

## 3. Configure and find the access address

**On Spark:** open <http://127.0.0.1:8767>. The desktop tray's **Open dashboard** item opens the same local address.

**On other devices:** use Tailscale HTTPS Serve. First inspect existing routing on Spark:

```bash
tailscale serve status
```

If the dashboard is already configured, use the HTTPS URL shown. It normally has the form `https://machine-name.tailnet-name.ts.net`; each installation has its own address. No separate domain purchase is required.

For a new route, **only if HTTPS port 443 is unused**, run:

```bash
sudo tailscale serve --bg --https=443 http://127.0.0.1:8767
tailscale serve status
```

If Tailscale requests Serve/HTTPS activation, an administrator of that account must complete it. Do not overwrite an existing 443 service. To use an available 8443 port instead, specify `--https=8443` and use the resulting URL including its port. Do not enable Funnel for public internet access.

Installation and updates do not rename the Tailscale device or change an existing access address. The dashboard's Spark name setting is a **display label**, separate from its address and OS hostname.

Alternative access through SSH forwarding:

```bash
ssh -N -L 8767:127.0.0.1:8767 USER@SPARK_TAILSCALE_NAME
```

Replace `USER` and `SPARK_TAILSCALE_NAME` with your actual values. Open <http://127.0.0.1:8767> in the browser on the device running that SSH command.

## 4. Sign-in and password recovery

Sign in with the password chosen during installation. On the same browser and access address, your device stays signed in without a fixed expiry, including server restarts and updates. The browser stores a random session secret, not your password; the server stores only its hash.

- Logout, a password reset or clearing browser data requires another sign-in.
- A different browser, URL or private browsing window has separate storage and may require a new sign-in.
- Up to 32 sessions are retained. Issuing a 33rd session removes the oldest one.

If you forget the password, use **Reset password** in the Spark desktop tray while logged into the local OS account, or run:

```bash
python3 ~/.local/share/dgx-spark-control-app/current/scripts/set-password.py
systemctl --user restart dgx-spark-control
```

The previous web password is not required. Existing device sessions are revoked. Never publish passwords, maintenance tokens, `password.json` or `sessions.json` in GitHub or shared documents.

## 5. Dashboard and readings

| Card | Meaning |
|---|---|
| GPU | Utilization and supported SM clock |
| CPU | Utilization, per-core details and readable clock range |
| Unified memory | OS used/total memory and supported memory clock |
| SSD | Root `/` filesystem used, total, user-available and reserved-free space |
| GPU temperature | GPU temperature supplied by the driver |
| GPU power | GPU power sensor reading, not whole-system wall power |
| Network traffic | Receive/send MB/s for physical interfaces; not isolated internet traffic |
| Disk I/O | Physical-disk read/write MB/s |

Click a card for real history and details. Unsupported or not-yet-available readings show `—`. Installed memory is detected from readable firmware information; otherwise the UI explicitly shows the OS total. It does not assume or round to a marketed 128 GB capacity. SSD used/total percentage can differ from Linux `df` percentage because of reserved space.

Saving the Spark display name in Settings updates it for all clients. Language and appearance preferences are local to each browser. Version 0.1.2 uses SVG arrows to avoid iOS emoji substitution.

## 6. Model-management scope

Version 0.1 controls only existing **user systemd services** explicitly registered in configuration. Model-folder scanning finds candidates within configured roots; it does not install, delete or register models automatically. A service being `active` does not prove inference readiness.

Follow the [model integration contract](MODELS.md). Back up your existing `config.json` and preserve its other fields while editing `models` and `model_roots`. Replace example paths and service names with your real installation values.

```json
{
  "models": [
    {"id": "my-llm", "name": "My LLM", "engine": "llama.cpp", "service": "my-llm.service", "allow_control": true}
  ],
  "model_roots": ["/your/configured/models"]
}
```

Do not replace the entire configuration file with this fragment. Restart only the dashboard service after manual configuration edits. Model installation and inference validation are separate tasks. Tokens/s, TTFT, request queues and automatic model switching require future engine adapters.

## 7. Desktop tray and startup

The GNOME tray provides dashboard open, display-name change, password reset, server start/restart and status. It requires GTK3, Python GI, Ayatana AppIndicator and a desktop session. See the [desktop reference](DESKTOP.md) for dependency/setup details. Closing the tray leaves the web server running.

If dependencies are missing, install them from the official Ubuntu repositories. The Ubuntu AppIndicators GNOME extension must also be enabled. The installer does not change these system settings automatically.

```bash
sudo apt-get install --no-install-recommends python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
bash ~/.local/share/dgx-spark-control-app/current/scripts/start-tray.sh
```

To run the server after reboot before OS login, an administrator can enable lingering when needed:

```bash
loginctl show-user "$USER" -p Linger
sudo loginctl enable-linger "$USER"
```

The tray starts after desktop login. A headless installation can run the web server without the tray.

## 8. Update and rollback

Read the target release notes, then run on Spark:

```bash
bash ~/.local/share/dgx-spark-control-app/current/update.sh 0.1.2
```

The updater downloads the published archive, verifies SHA256, installs it and runs an authenticated health check. Configuration, password hashes and device sessions live outside release code and are preserved. Models and drivers are not replaced.

Restore the previous code version:

```bash
bash ~/.local/share/dgx-spark-control-app/current/scripts/rollback.sh
```

Versions 0.1.1 and 0.1.2 share the same configuration schema. Version 0.1.0 predates password login and the tray, so its recovery behavior differs. Read the [update policy](UPDATES.md) before reverting.

## 9. Troubleshooting and resource limits

```bash
systemctl --user status dgx-spark-control
journalctl --user -u dgx-spark-control -n 50
tailscale serve status
systemctl --user show dgx-spark-control.slice -p MemoryCurrent -p MemoryPeak -p MemoryMax
```

For connection failures, check server state, the client's Tailscale connection/access policy, then the Serve address. Refresh the page if an older UI is visible. After a password reset, sign in with the new password.

The combined server/tray hard limit is **480 MiB = 503,316,480 bytes**, with no swap. Browsers, Tailscale and model engines are outside this budget. Collection is shared across clients at most once every five seconds and stops when there are no requests. Consult the [release validation record](releases/0.1.2.md) for measured evidence and untested scenarios.

## 10. Continue development with another LLM

Start with [AGENTS.md](../AGENTS.md), then [architecture](ARCHITECTURE.md), [model integration](MODELS.md) and [update policy](UPDATES.md). For each release, align VERSION, CHANGELOG, validation records, both language guides, GitHub Release and Notion records. Do not publish real credentials, private model paths or raw logs.
