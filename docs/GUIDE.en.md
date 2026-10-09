# DGX-SPARK-Control user guide — English

**0.2.1** · [한국어](GUIDE.ko.md) · [Easy installation](QUICKSTART.en.md)

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
| Unified memory | OS used/total memory, supported memory clock |
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

Existing user systemd services must be explicitly registered in `config.json` before control is allowed. Model discovery lists file candidates under configured paths. It does not download, delete, register or switch models automatically. Service `active` is different from inference readiness.

Read [Model integration](MODELS.md), back up configuration, preserve its other fields and add only the intended models. Inference tok/s, TTFT and global queues require future adapters.

## Updates, resources and troubleshooting

Update a `.deb` installation by installing the newer `.deb`. Do not mix package and legacy script update methods. [Updates, recovery and migration](UPDATES.md).

```bash
systemctl --user status dgx-spark-control
journalctl --user -u dgx-spark-control -n 50
tailscale serve status
systemctl --user show dgx-spark-control.slice -p MemoryCurrent -p MemoryPeak -p MemoryMax
```

The server and tray share a 480 MiB limit with no swap. Browsers, models, setup and Tailscale are separate. There is no telemetry collection without client requests. Long-running inference impact requires a separate benchmark.

For another LLM continuing development, read [AGENTS.md](../AGENTS.md), [Architecture](ARCHITECTURE.md), [Models](MODELS.md) and [Updates](UPDATES.md). Keep secrets out of public materials. [This release's validation](releases/0.2.1.md).

## Korean web font / iPhone

The Korean web UI uses SUIT 2.0.5. Regular (400), SemiBold (600) and Bold (700) WOFF2 files are served by your Spark, with no iPhone font installation or external font CDN required. Rajdhani remains the numeric/English display font and Chakra Petch remains the English UI font. System Korean fonts appear while the web font loads or if loading fails.

Safari supports WOFF2 web fonts, although glyph rendering may differ slightly between Windows and iPhone. [WebKit font support](https://webkit.org/blog/6643/improved-font-loading/). Refresh the page after updating if the old typeface remains. Native GTK setup/tray typography is outside this change.
