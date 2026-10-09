# Easy installation on DGX Spark — English

**0.2.1 · Ubuntu 24.04 / ARM64** · [한국어](QUICKSTART.ko.md)

## 1. Download the installer

Download **dgx-spark-control_0.2.1_arm64.deb** to your Spark from [GitHub Releases](https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/tag/v0.2.1).

Open it in your software installer and choose **Install**. Administrator authentication may be required. GTK and tray dependencies are installed from Ubuntu repositories. Internet access is required; models, CUDA and NVIDIA drivers are not replaced.

If no graphical package installer is available, or you prefer a terminal, run this from the download folder:

```bash
sudo apt install ./dgx-spark-control_0.2.1_arm64.deb
```

Include `./`. Change to the actual download directory first. Run the following initial setup **as your normal user, without sudo**.

## 2. Open initial setup

Find **DGX-SPARK-Control Setup** in the Spark application menu, or run:

```bash
dgx-spark-control setup
```

Follow **Language → Spark display name and password → Connection check → Save & start**.

- New installation: enter the password twice. Typed characters are hidden.
- Existing installation: the current name is prefilled. Leave both password fields blank to keep your password and remembered device logins.
- Changing the password signs out existing devices.
- When complete, choose **Open dashboard** or **Copy address**.
- Closing setup leaves the server running. The wizard does not stay in the background.

## 3. Connect from another device

On Spark itself use **http://127.0.0.1:8767**. Entering that local address on a phone does not connect it to Spark.

Other devices use the Spark's **Tailscale HTTPS address**. Existing dashboard routes are detected and can be copied from setup or the tray. Spark and the client must be on the same Tailscale network with access allowed.

If Tailscale is missing, follow the [official Linux instructions](https://tailscale.com/download/linux) and sign in. After completing initial setup, first check:

```bash
tailscale serve status
```

Keep existing routes. Run the following **only if HTTPS port 443 is unused**:

```bash
sudo tailscale serve --bg --https=443 http://127.0.0.1:8767
tailscale serve status
```

If your account needs HTTPS/Serve approval, complete it in the browser. If 443 serves another application, use an available 8443 port and use the printed URL including that port. **Do not enable Funnel.** Setup does not sign in, approve access on your behalf, or replace existing routes.

## 4. Tray and automatic startup

Tray actions: open dashboard, copy address, setup, check for updates, rename, reset password, start/restart server, status and close tray.

- **Check for updates** opens GitHub Releases. There is no automatic installation or periodic update polling.
- If the icon is absent, enable **Ubuntu AppIndicators** in GNOME Extensions. Browser access remains available.
- The dashboard is registered as a user service. To start it before OS login, an administrator can run once:

```bash
sudo loginctl enable-linger "$USER"
```

The tray starts after desktop login. If you forget the password, use **Reset password** in the tray. Your local OS account can reset it without the old web password.

## 5. Update or remove

Download a newer `.deb` and install it the same way. Activated package-managed dashboards with running user managers restart. Logged-out users receive the new code on their next service start. Spark name, password, remembered logins and model registrations are retained.

Do not mix the old `update.sh` or `rollback.sh` with a package-managed installation. See [Updates](UPDATES.md) for recovery and migration from archive installations.

Remove the application:

```bash
sudo apt remove dgx-spark-control
```

Active user dashboards stop and application files are removed. User settings, password, remembered logins and old archive code backups remain. Registrations for users logged out during removal may also remain; the server cannot start without the executable. Models, drivers and Tailscale are not removed.

## 6. SSH and LLM installation

Ask the LLM to read this guide and [AGENTS.md](../AGENTS.md). It needs terminal/SSH access.

```bash
dgx-spark-control setup --check
dgx-spark-control setup --cli --lang en
```

`--check` produces read-only JSON diagnostics. Enter a new installation password in an interactive terminal. Never put it in command-line arguments, chat or logs.

Only installations with an **existing password** can migrate or activate without input:

```bash
dgx-spark-control setup --non-interactive
```

On a fresh installation, this exits with code 2 and `setup_required`, without starting the server. The user completes any required Tailscale approval or administrator authentication.

## Troubleshooting

```bash
systemctl --user status dgx-spark-control
journalctl --user -u dgx-spark-control -n 50
tailscale serve status
systemctl --user show dgx-spark-control.slice -p MemoryCurrent -p MemoryMax
```

Server + tray have a **480 MiB** combined limit. Setup, browsers, model engines and Tailscale are outside that budget. This release targets DGX Spark Ubuntu ARM64; Windows and other platforms are on hold.

[Full user guide](GUIDE.en.md) · [Validation and limitations](releases/0.2.1.md)
