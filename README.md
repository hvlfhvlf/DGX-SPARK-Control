# DGX-SPARK-Control

**User guide / 사용자 가이드: [한국어](docs/GUIDE.ko.md) | [English](docs/GUIDE.en.md)**

Version **0.1.2** · lightweight web monitoring and registered-service control for NVIDIA DGX Spark.

한국어: Spark 안에서 실행되는 웹 서버입니다. 기본 이름은 `DGX_SPARK`이며 설정에서 변경하면 서버에 저장되어 다른 접속 기기에도 반영됩니다. 공개 디자인 미리보기와 실제 설치판은 별개입니다.

## Install on Spark

Requires Linux, Python **3.12+**, a user systemd session, and an NVIDIA driver for GPU readings. DGX Spark / Ubuntu 24.04 ARM64 is the first validation target. No pip, npm, Docker, database server or separate monitoring agent is required.

Download `DGX-SPARK-Control-0.1.2.tar.gz` and `SHA256SUMS` from [Releases](https://github.com/hvlfhvlf/DGX-SPARK-Control/releases), verify the checksum, extract into an empty directory, and run:

```bash
curl -fLO https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/download/v0.1.2/DGX-SPARK-Control-0.1.2.tar.gz
curl -fLO https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/download/v0.1.2/SHA256SUMS
sha256sum -c SHA256SUMS
mkdir dgx-spark-control-install
tar -xzf DGX-SPARK-Control-0.1.2.tar.gz -C dgx-spark-control-install
cd dgx-spark-control-install
bash install.sh
```

Interactive installation asks you to choose and confirm a password. On Spark open **http://127.0.0.1:8767** and sign in with that password. This device remains signed in across browser close and server updates until logout or password reset. Only a random session secret is kept in browser localStorage; the password is never stored there.

Forgotten password? Reset it from the Spark desktop tray, or the local terminal (no old password needed):

```bash
python3 ~/.local/share/dgx-spark-control-app/current/scripts/set-password.py
systemctl --user restart dgx-spark-control
```

Non-interactive installations keep private token access until a local password is set. Never publish passwords, access-token, password.json or sessions.json. [Password and desktop guide](docs/DESKTOP.md).

For Tailscale HTTPS, boot startup and troubleshooting, see [INSTALL.md](docs/INSTALL.md).

## Low overhead by design

- Server: one Python process, standard library only; NVML through a cached native-library session. Optional GTK tray for local settings, with no telemetry polling.
- Metrics are collected on demand, shared across clients, at most once every five seconds.
- No browser requests means no telemetry collection. Hidden browser tabs stop polling.
- At most 720 samples (one hour), 200 control events, 8 HTTP workers.
- Combined server + tray slice: `MemoryMax=480M`, `MemorySwapMax=0` (480 MiB = 503,316,480 bytes, below 512 MB).
- These limits apply to the dashboard service cgroup, not inference engines started through systemd, the remote browser or Tailscale.
- A hard limit is protection, not proof of normal memory use. See [validation](docs/releases/0.1.2.md) for measured evidence and remaining limitations.

## 0.1 functionality

Live GPU/CPU utilization, UMA memory, GPU temperature/power, available clocks, filesystem usage, physical-network and physical-disk I/O; bounded real-history detail windows; shared Spark display name; user-systemd service start/stop from an explicit registry; bounded on-demand model candidate search.

Hardware identity and RAM size are detected: readable SMBIOS installed capacity, otherwise explicitly labeled OS usable total. No assumed 128 GB. SSD usage means the root filesystem; details distinguish used, user-available and reserved space. Desktop tray setup is optional; see [DESKTOP.md](docs/DESKTOP.md).

Inference tok/s, engine readiness, global request queues, installation/removal of model weights and automatic model switching are **not connected in 0.1**. Their UI never presents simulated values in the installed runtime. Missing sensors display `—`. Service `active` does not prove model readiness.

## Updates and continuation

```bash
# Select the release deliberately, never silently track an unreviewed branch.
bash ~/.local/share/dgx-spark-control-app/current/update.sh 0.1.2
```

Configuration, access token and existing models survive updates. Each update keeps the previous code and a configuration backup. [Update/rollback guide](docs/UPDATES.md).

Start here when continuing with another LLM: [AGENTS.md](AGENTS.md), [architecture](docs/ARCHITECTURE.md), [model adapters](docs/MODELS.md), [changelog](CHANGELOG.md).

Bundled typefaces retain their original OFL license files under `web/fonts`. This repository contains original dashboard code, not Marathon game assets. A general source license has not yet been selected by the owner.
