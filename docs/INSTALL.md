# Technical installation / 기술 설치 안내 — 0.2.0

Start with [한국어 간편 설치](QUICKSTART.ko.md) or [English quick start](QUICKSTART.en.md).

Target: NVIDIA DGX Spark, Ubuntu 24.04 ARM64, Python 3.12+, user systemd and cgroup v2. Other platforms are on hold.

## File ownership

| Path | Owner and role |
|---|---|
| `/usr/lib/dgx-spark-control` | dpkg-owned code, docs and assets |
| `/usr/bin/dgx-spark-control` | package launcher |
| `/usr/share/applications/dgx-spark-control.desktop` | initial setup application |
| `~/.local/share/dgx-spark-control` | private user settings, authentication and backups |
| `~/.local/share/dgx-spark-control/package-managed` | user opted into package services |
| `~/.local/share/dgx-spark-control-app/current` | alias to package code after migration |
| `~/.local/share/dgx-spark-control-app/previous` | preserved archive code for migration recovery |
| `~/.config/systemd/user/dgx-spark-control.*` | bounded dashboard user units |
| `~/.config/autostart/dgx-spark-control-tray.desktop` | tray after desktop login |

Install the `.deb` with an administrator, then run setup as the desktop user. Package maintainer scripts never prompt for a web password. Fresh setup saves the password before activation. Existing-password noninteractive setup preserves auth data. The installer does not enable Tailscale Serve/Funnel or lingering itself; instructions are shown only as needed.

## Archive alternative

Download `DGX-SPARK-Control-0.2.0.tar.gz` and `SHA256SUMS` from the release. Verify only the archive's checksum line if you did not download the `.deb`:

```bash
grep '  DGX-SPARK-Control-0.2.0.tar.gz$' SHA256SUMS | sha256sum -c -
mkdir app
tar -xzf DGX-SPARK-Control-0.2.0.tar.gz -C app
cd app
python3 -m spark_control.setup --cli --lang en
```

Use `--lang ko` for Korean. Run as your normal user, not root. Archives need their Python/systemd dependencies present; optional GTK/tray dependencies are documented in [Desktop](DESKTOP.md). Existing archive updates still support `bash install.sh` when the private password already exists. Fresh noninteractive installs fail closed with exit code 2.

Use Tailscale HTTPS or SSH forwarding for other devices:

```bash
ssh -N -L 8767:127.0.0.1:8767 USER@SPARK_TAILSCALE_NAME
```

The browser on that client can then use `http://127.0.0.1:8767`. Keep the server bound to localhost. Do not publish the live control panel to the prototype hosting site.

[Update, migration and removal](UPDATES.md) · [한국어 사용자 가이드](GUIDE.ko.md) · [English user guide](GUIDE.en.md)
