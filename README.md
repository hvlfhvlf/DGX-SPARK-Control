# DGX-SPARK-Control

**0.3.4 · NVIDIA DGX Spark · Ubuntu 24.04 ARM64**

Measured inference throughput, reviewed service registration, model-file inventory and compact live views. 실측 추론 처리량·서비스 등록·모델 파일 목록·실시간 상태를 한곳에서 확인합니다.

**간편 설치: [한국어](docs/QUICKSTART.ko.md) | Easy installation: [English](docs/QUICKSTART.en.md)**

**사용자 가이드: [한국어](docs/GUIDE.ko.md) | User guide: [English](docs/GUIDE.en.md)**

A lightweight dashboard hosted on your Spark, accessed through your browser and Tailscale. 한국어·영어 설정 마법사, 실제 하드웨어 상태, 로컬 트레이, 등록한 모델 서비스 제어를 제공합니다.

> New in 0.3.4: service boot autostart uses the same rectangular switch as Settings, with keyboard access, a 44px touch target and distinct unavailable/saving states.
> 0.3.4: 서비스 부팅 자동 시작을 설정 화면과 동일한 사각 스위치로 통일했습니다. 키보드 조작, 44px 터치 영역, 저장 중·사용 불가 상태를 유지합니다.

## Install / 설치

1. Download **dgx-spark-control_0.3.4_arm64.deb** from [Releases](https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/tag/v0.3.4) onto Spark. Spark에 설치 파일을 다운로드합니다.
2. Open it in the software installer, or run the following in its download folder. 파일을 열어 설치하거나 다운로드 폴더에서 실행합니다:

```bash
sudo apt install ./dgx-spark-control_0.3.4_arm64.deb
```

3. Open **DGX-SPARK-Control Setup / 초기 설정** from Applications, or run as your normal user (without sudo):

```bash
dgx-spark-control setup
```

Language → name/password → connection check → Save & start. 언어 → 이름·비밀번호 → 연결 확인 → 저장하고 시작.

On Spark: **http://127.0.0.1:8767**. Other devices use the detected Tailscale HTTPS address. Tailscale sign-in/Serve approval is a separate, one-time step; setup keeps existing routes. [한국어 연결 안내](docs/QUICKSTART.ko.md#3-다른-기기에서-접속하기) · [Connection instructions](docs/QUICKSTART.en.md#3-connect-from-another-device).

GTK/tray dependencies come from Ubuntu repositories. A graphical package opener is optional; the apt command works without one. Tailscale, model engines and NVIDIA drivers are not bundled or replaced. GNOME may need Ubuntu AppIndicators enabled. Windows and other platform ports are on hold.

## SSH / LLM

**LLM에게 전달할 안내서 / Agent playbooks: [한국어](docs/LLM-GUIDE.ko.md) | [English](docs/LLM-GUIDE.en.md)**

Copyable prompts cover installation, existing-service registration, display edits and actual model replacement, with verification and recovery. 설치·등록·표시 수정·실제 모델 교체별 요청문과 검증·복구 절차를 제공합니다.


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

Application updates are separate: Model Bay → Details supports explicitly configured Harness/Hermes/ComfyUI installations. Stop the app yourself before confirming an update. Checking creates no backup; applying retains one successful managed recovery backup per service. Failed recovery needs local review. [Setup and limits](docs/SERVICE-UPDATES.md).

앱 업데이트는 대시보드 패키지 업데이트와 별개입니다. 지원 설치본을 로컬에서 연결한 뒤 상세창에서 확인·적용하며 실행 중에는 차단합니다. [한글 사용 안내](docs/GUIDE.ko.md#앱-업데이트-034).

The archive remains available for existing script installations; do not mix update methods. [Technical installation guide](docs/INSTALL.md).

## Low overhead

- One standard-library Python server; optional GTK tray with no telemetry polling.
- On-demand shared metrics at most once per five seconds; no client requests means no collection.
- Server + tray combined limit: **480 MiB = 503,316,480 bytes**, no swap. Models, browsers, setup and Tailscale are outside this budget.
- No pip, npm, Docker, database server or resident LLM required for the dashboard. Optional application updates use the existing app toolchain in a temporary worker (up to 2 GiB), outside the 480 MiB monitoring limit; see [service updates](docs/SERVICE-UPDATES.md).
- Hard limits are not performance proof. [Actual validation and limitations](docs/releases/0.3.4.md).

## Features and limits

Live GPU/CPU utilization, unified memory, GPU temperature/power, supported clocks, root filesystem usage, physical network/disk I/O, real-history details, shared display name, explicit user-service controls and bounded model candidate discovery. Unsupported measurements display `—`.

Service/profile registration, start/stop/restart, stopped-profile selection, display-label editing, shared card ordering and on-demand service discovery are available. Supported TensorFold/vLLM/Strata endpoints provide measured throughput; existing user services can be registered through the web UI. ComfyUI queue counts and LLM readiness remain separate from process state. Global queues, engine-specific model load/unload, automatic installation/deletion and automatic switch rollback are not implemented. [Model guide](docs/MODELS.md).

## Privacy / 개인정보

No API keys, passwords, personal service addresses or model files are shipped. Credentials and service registrations are created on each Spark and remain outside package-managed code. No analytics or automatic telemetry upload is included. [Data flow and release audit scope](docs/PRIVACY.md).

API 키·개인 주소·비밀번호는 배포하지 않습니다. 새 설치의 서비스 목록은 비어 있으며 각 기기에서 등록합니다. 설치기는 모델 엔진·ComfyUI 접속 게이트웨이·포트 공개를 자동 설정하지 않습니다.

## Development

Read [AGENTS.md](AGENTS.md), [Architecture](docs/ARCHITECTURE.md), [Updates](docs/UPDATES.md), and [Changelog](CHANGELOG.md).

Bundled fonts retain their OFL licenses in `web/fonts`. This is original dashboard code, without Marathon game assets. A general source license has not yet been selected by the owner.
