# DGX-SPARK-Control

**0.2.1 · NVIDIA DGX Spark · Ubuntu 24.04 ARM64**

**간편 설치: [한국어](docs/QUICKSTART.ko.md) | Easy installation: [English](docs/QUICKSTART.en.md)**

**사용자 가이드: [한국어](docs/GUIDE.ko.md) | User guide: [English](docs/GUIDE.en.md)**

A lightweight dashboard hosted on your Spark, accessed through your browser and Tailscale. 한국어·영어 설정 마법사, 실제 하드웨어 상태, 로컬 트레이, 등록한 모델 서비스 제어를 제공합니다.

## Install / 설치

1. Download **dgx-spark-control_0.2.1_arm64.deb** from [Releases](https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/tag/v0.2.1) onto Spark. Spark에 설치 파일을 다운로드합니다.
2. Open it in the software installer, or run the following in its download folder. 파일을 열어 설치하거나 다운로드 폴더에서 실행합니다:

```bash
sudo apt install ./dgx-spark-control_0.2.1_arm64.deb
```

3. Open **DGX-SPARK-Control Setup / 초기 설정** from Applications, or run as your normal user (without sudo):

```bash
dgx-spark-control setup
```

Language → name/password → connection check → Save & start. 언어 → 이름·비밀번호 → 연결 확인 → 저장하고 시작.

On Spark: **http://127.0.0.1:8767**. Other devices use the detected Tailscale HTTPS address. Tailscale sign-in/Serve approval is a separate, one-time step; setup keeps existing routes. [한국어 연결 안내](docs/QUICKSTART.ko.md#3-다른-기기에서-접속하기) · [Connection instructions](docs/QUICKSTART.en.md#3-connect-from-another-device).

GTK/tray dependencies come from Ubuntu repositories. A graphical package opener is optional; the apt command works without one. Tailscale, model engines and NVIDIA drivers are not bundled or replaced. GNOME may need Ubuntu AppIndicators enabled. Windows and other platform ports are on hold.

## SSH / LLM

```bash
dgx-spark-control setup --check
dgx-spark-control setup --cli --lang en
```

Use `--lang ko` for Korean. `--check` is read-only JSON. A fresh setup requires interactive password entry. For existing-password migration only:

```bash
dgx-spark-control setup --non-interactive
```

Never put passwords in command arguments or chat. 비밀번호는 명령줄이나 채팅에 입력하지 않습니다.

## Updates / 업데이트

Install the new `.deb` using apt. Keep settings, password, remembered browser logins and model registrations. 새 패키지 설치 시 기존 설정과 로그인을 보존합니다. The tray's update action opens the release page; it does not silently install anything. [Migration, rollback and removal](docs/UPDATES.md).

The archive remains available for existing script installations; do not mix update methods. [Technical installation guide](docs/INSTALL.md).

## Low overhead

- One standard-library Python server; optional GTK tray with no telemetry polling.
- On-demand shared metrics at most once per five seconds; no client requests means no collection.
- Server + tray combined limit: **480 MiB = 503,316,480 bytes**, no swap. Models, browsers, setup and Tailscale are outside this budget.
- No pip, npm, Docker, database server or resident LLM required.
- Hard limits are not performance proof. [Actual validation and limitations](docs/releases/0.2.1.md).

## Features and limits

Live GPU/CPU utilization, unified memory, GPU temperature/power, supported clocks, root filesystem usage, physical network/disk I/O, real-history details, shared display name, explicit user-service controls and bounded model candidate discovery. Unsupported measurements display `—`.

Inference speed, engine readiness, global job queues and automatic model installation/deletion/switching still need engine adapters. Models must be explicitly registered; service active does not prove inference readiness. [Model guide](docs/MODELS.md).

## Development

Read [AGENTS.md](AGENTS.md), [Architecture](docs/ARCHITECTURE.md), [Updates](docs/UPDATES.md), and [Changelog](CHANGELOG.md).

Bundled fonts retain their OFL licenses in `web/fonts`. This is original dashboard code, without Marathon game assets. A general source license has not yet been selected by the owner.
