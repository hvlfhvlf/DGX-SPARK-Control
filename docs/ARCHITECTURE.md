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
```

## 파일별 책임

- `spark_control/server.py`: 정적 웹, 인증, Origin 검증, bounded HTTP worker, API 라우팅.
- `config.py`: config schema 1, 초기값 `DGX_SPARK`, 원자적 저장, 토큰 생성.
- `metrics.py`: 5초 캐시, CPU delta, 공유 메모리, GPU NVML, 센서 식별자, 물리 NIC/디스크 I/O, deque 이력.
- `models.py`: 서비스 레지스트리, 시작/정지 요청, 10초 상태 캐시, 명시적 경로 검색.
- `web/runtime.js`: 실측 운영 UI. 서버 데이터와 브라우저 개인화를 구분한다.
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

## API

공개 GET `/api/info`: 버전·live 모드·인증 필요 여부만 제공한다. 그 외 `/api/*`는 `Authorization: Bearer <token>` 필요.

| Endpoint | 동작 |
|---|---|
| GET `/api/settings` | 서버 이름·버전 |
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
