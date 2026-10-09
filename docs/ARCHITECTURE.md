# 작동 구조 / Architecture

## 설계 목표

서버는 Spark에서 실행한다. 다른 기기는 브라우저로 접근한다. 대시보드 전체 서비스의 메모리 상한은 512 MB 미만이며, 모델·드라이버·접속 기기의 브라우저는 별도 자원이다. 0.1은 Python 표준 라이브러리만 사용한다. 추론 모델이나 별도 LLM 에이전트를 실행하지 않는다.

```text
Browser (static JS, charts, personal appearance)
  → HTTPS Tailscale Serve or SSH tunnel
  → 127.0.0.1:8767 — Python HTTP server (8 workers max)
      ├─ Config: atomic JSON + private token file
      ├─ Collector: cached NVML session, /proc, /sys, statvfs
      ├─ History: deque 720 samples, memory only
      └─ Models: explicit user-systemd service allowlist
Optional GTK tray → local settings/password recovery (no telemetry polling)
Server + tray → dgx-spark-control.slice (combined 480 MiB limit)
```

## 파일별 책임

- 0.2: `.deb` owns `/usr/lib/dgx-spark-control`; `/usr/bin/dgx-spark-control` dispatches fixed actions. Private settings stay in the existing user directory. Setup saves a first password before activation; existing auth data is retained.
- `setup.py`: read-only preflight/state, validation, user-unit migration with backups and authenticated version-aware health check; CLI and existing-password-only noninteractive mode.
- `wizard.py`: transient GTK3 four-step setup with Korean/English dictionaries; no embedded browser or polling agent.
- `desktop.py`: one-shot Tailscale dashboard-route detection and separate desktop launch helpers; never changes Serve/Funnel.
- `packaging/session-maintenance.py`: dpkg hook refreshes only opted-in user managers as their own users; removal preserves private data. `scripts/build-deb.py` creates the ARM64 package without root.
- Package updates use apt/dpkg; archive update/rollback scripts refuse package-managed installs. The current alias points to package code, previous retains the pre-migration archive. First-run GUI/CLI and checks are outside the monitoring slice and exit when done.

- `spark_control/server.py`: 정적 웹, 인증, Origin 검증, bounded HTTP worker, API 라우팅.
- `config.py`: config schema 1, 초기값 `DGX_SPARK`, 원자적 저장, 토큰 생성.
- `metrics.py`: 5초 캐시, CPU delta, 공유 메모리, GPU NVML, 센서 식별자, 물리 NIC/디스크 I/O, deque 이력.
- `models.py`: 서비스 레지스트리, 시작/정지 요청, 10초 상태 캐시, 명시적 경로 검색.
- `hardware.py`: 펌웨어 설치 용량과 OS MemTotal, NVML GPU 이름, 아키텍처·코어 수. 재시작 시 한 번 읽는 인벤토리.
- `sessions.py`: 최대 32개 세션의 해시를 원자적으로 저장. 고정 만료 없음. 비밀번호 기록의 fingerprint가 바뀌면 기존 세션 무효화.
- `tray.py`: 선택적 GTK/AppIndicator 데스크톱 메뉴. 정기 수집 없음, 로컬 OS 사용자 권한으로 비밀번호 복구 가능.
- `web/runtime.js`: 실측 운영 UI. 서버 데이터와 브라우저 개인화를 구분한다.
- UI 화살표는 `web/app.js`의 `arrowIcon()`과 정적 헤더의 같은 SVG path를 사용한다. `currentColor`로 기존 색/호버를 따르고 장식 아이콘은 `aria-hidden`으로 처리한다. 도식 크기 규칙은 `.hero-art > svg`에만 적용하여 라벨 아이콘에 전파하지 않는다. 문자는 OS 이모지로 대체될 수 있으므로 화살표 아이콘에 쓰지 않는다.
- `web/app.js`, `metric-details.js`: 기존 디자인 기반·모달 모션. 모의 갱신은 설치판에서 비활성화한다. 후속 버전에서 순수 UI 모듈로 분리할 수 있다.
- `install.sh`, `update.sh`, `scripts/rollback.sh`: 배포·버전 변경. 사용자 데이터는 코드 밖에 저장.

## 메트릭 계약

`GET /api/metrics`: UNIX timestamp, GPU/CPU 퍼센트, memory GiB, disk TiB, power W, temp °C, 클럭 MHz/GHz, network/diskio `[receive/read, send/write]` MB/s. Byte 기반 MB/s이며 Mbps가 아니다.

- 값 `null`은 미지원 또는 delta 준비 중이다. 0은 실제 영 값이다.
- CPU guest 시간 중복 합산 금지. CPU/GPU의 공유 메모리 용량을 더하지 않는다.
- 물리 NIC만 합산해 Tailscale/bridge 중복 방지. 전체 물리 block device만 합산해 partition 중복 방지.
- 15초 이상 수집 공백은 rate baseline을 새로 잡는다. 이력 그래프의 공백을 보간해서 실측처럼 표시하지 않는다.
- 센서는 원래 hwmon source와 label을 표시한다. ACPI를 CPU/SoC라고 임의 명명하지 않는다.
- GPU 전력은 `nvmlDeviceGetPowerUsage` 반환값이다. 전체 시스템/벽전력으로 표시하지 않는다. 센서별 평균/순간 의미는 드라이버에 따르므로 UI는 GPU 전력으로 표시한다.
- SSD는 `/` 파일시스템 statvfs. used=(blocks-bfree)*frsize, available=bavail*frsize, reserved-free=(bfree-bavail)*frsize. 카드 게이지는 used/total이며 df 퍼센트는 ceil(used/(used+available)*100)로 구분한다. 원시 SSD 용량과 같다고 표시하지 않는다.
- RAM은 firmware installed bytes와 OS usable bytes를 별도로 제공. UI는 정확한 GiB 환산을 사용하며 OS 값을 임의로 64/128에 맞춰 반올림하지 않는다.

## API

공개 GET `/api/info`: 버전·live 모드·인증 필요 여부만 제공한다. POST `/api/login`은 비밀번호를 검증하여 세션을 발급한다. 나머지 `/api/*`는 `Authorization: Bearer <token>`이 필요하다.

| Endpoint | 동작 |
|---|---|
| GET `/api/settings` | 서버 이름·버전 |
| POST `/api/login` | 비밀번호 확인, 무기한 기기 세션 발급 (원문 저장 없음) |
| POST `/api/logout` | 현재 세션 폐기 |
| GET `/api/hardware` | 실제 GPU/CPU 아키텍처·코어·설치/OS 메모리 |
| POST `/api/settings` | `{spark_name}` 1–32자 저장 |
| GET `/api/metrics` | 최대 5초당 1회 수집, 여러 요청 결과 공유 |
| GET `/api/history` | 실제 최근 1시간 이력, 최대 720 |
| GET `/api/models` | 등록 서비스 상태 (준비 상태와 구분) |
| POST `/api/models/action` | `{id,action:start/stop}` allowlist 제어 |
| POST `/api/models/discover` | 지정 경로 후보 검색, 설치/등록 자동 실행 없음 |
| GET `/api/events` | 이번 서버 실행 중 제어 사건, 최대 200 |
| GET `/api/health` | 상태·버전·실제 수집 횟수·상한 |

## 자원 한도와 보안

프로세스 수 1, HTTP worker 8, 요청 본문 4 KiB, 이력 720, 제어 사건 200, 등록 모델 32, 검색 루트 8, 깊이 5, 파일 검사 10,000/2초, 결과 128. 검색은 사용자가 누를 때만 실행한다. 파일 가중치를 읽거나 해시하지 않는다.

서비스 cgroup `MemoryMax=480M`은 503,316,480 bytes, `MemorySwapMax=0`. `MemoryHigh=192M`은 회수 압력을 주는 soft threshold이다. OOM 시 서비스가 재시작될 수 있으므로 이력은 손실될 수 있다. hard cap은 테스트를 대신하지 않는다.

정적 자산과 브라우저 애니메이션은 사용자 기기에서 렌더링한다. 모델 시작은 systemd에 요청하여 모델이 대시보드 cgroup 안에서 실행되지 않도록 한다. 이 때문에 512 MB 제한은 모델 메모리를 제한하지 않는다.

표준 라이브러리 HTTP 서버는 인터넷 공개 서비스로 사용하지 않는다. localhost + Tailscale/SSH, 인증, Origin 검증, CSP, 경로 경계 확인, thread/body 상한으로 범위를 제한한다. 토큰 및 config를 공개 저장소에 넣지 않는다.

비밀번호는 랜덤 salt + PBKDF2-HMAC-SHA256 600,000회 해시로 저장한다. 로그인 실패 30회/분 제한. 로그인 후 랜덤 세션을 브라우저 localStorage에, 그 SHA256만 서버 sessions.json(0600)에 보관한다. 고정 만료 없음은 사용자 요구사항이다. 재시작/업데이트는 보존하고 로그아웃/비밀번호 재설정은 해제한다. 최대 32기기를 넘으면 가장 오래 발급된 세션을 제거한다. 로컬 healthcheck/트레이는 0600 유지관리 토큰을 사용하며 원격 사용자 화면에 노출하지 않는다.

## Web typography

Korean UI uses self-hosted static SUIT 2.0.5 WOFF2 at 400/600/700. `--korean` supplies the fallback chain, `html[lang="ko"]` changes shared UI font tokens, and `--display` keeps Rajdhani numbers/English lettering. English UI retains Chakra Petch with SUIT for Korean glyph fallback. Native GTK typography is unchanged. Upstream source/license: `web/fonts/SUIT-SOURCE.md` and `SUIT-OFL.txt`.
