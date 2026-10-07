# DGX-SPARK-Control 사용자 가이드 — 한국어

버전 **0.1.2** · [English guide](GUIDE.en.md) · [설치 파일](https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/tag/v0.1.2)

Spark에서 실행하는 가벼운 웹 대시보드입니다. 브라우저로 실제 하드웨어 상태를 확인하고, 명시적으로 등록한 모델 서비스를 시작·정지합니다. 기본 표시 이름은 `DGX_SPARK`입니다.

## 1. 설치 준비

- 검증 환경: NVIDIA DGX Spark, Ubuntu 24.04, ARM64, Python 3.12 이상, 사용자 systemd와 cgroup v2.
- GPU 측정에는 NVIDIA 드라이버가 필요합니다. 설치 프로그램은 모델·CUDA·드라이버·Tailscale을 설치하거나 교체하지 않습니다.
- 웹 서버는 Python 표준 라이브러리만 사용합니다. pip, npm, Docker, 별도 DB나 LLM 에이전트가 필요하지 않습니다.
- 다른 기기에서 접속하려면 그 기기와 Spark가 접근 허용된 동일 Tailscale 네트워크에 연결되어 있어야 합니다.

## 2. Spark에 설치하기

Spark 터미널에서 **일반 사용자 계정**으로 실행합니다. `sudo bash install.sh`로 실행하지 마세요. 아래 명령은 새 작업 폴더를 만듭니다.

```bash
mkdir -p ~/Downloads
install_dir=$(mktemp -d "$HOME/Downloads/dgx-spark-control-0.1.2-XXXXXX")
cd "$install_dir"
curl -fLO https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/download/v0.1.2/DGX-SPARK-Control-0.1.2.tar.gz
curl -fLO https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/download/v0.1.2/SHA256SUMS
sha256sum -c SHA256SUMS
```

`OK`를 확인한 다음에만 압축을 풀고 설치합니다.

```bash
mkdir app
tar -xzf DGX-SPARK-Control-0.1.2.tar.gz -C app
cd app
bash install.sh
```

처음 대화형으로 설치하면 비밀번호를 두 번 입력합니다. 비밀번호 원문은 저장하지 않고 salt와 PBKDF2 해시를 저장합니다. 비대화형 설치는 비밀번호 설정 전까지 로컬 유지관리 토큰 방식으로 접근합니다. 설치가 끝나면 인증된 상태 검사를 자동으로 수행합니다.

## 3. 접속 주소 설정·확인

**Spark 자체:** 브라우저에서 <http://127.0.0.1:8767>을 엽니다. 데스크톱 트레이의 **대시보드 열기**도 같은 주소를 엽니다.

**다른 기기:** Tailscale HTTPS Serve로 접속합니다. 먼저 Spark에서 현재 설정을 확인합니다.

```bash
tailscale serve status
```

이미 이 대시보드가 연결되어 있다면 출력된 HTTPS 주소를 사용합니다. 주소는 일반적으로 `https://기기이름.네트워크이름.ts.net` 형태이며, 설치자마다 다릅니다. 별도 도메인 구매는 필요하지 않습니다.

새로 연결하며 **443 포트가 비어 있는 경우에만** 다음 명령을 사용합니다.

```bash
sudo tailscale serve --bg --https=443 http://127.0.0.1:8767
tailscale serve status
```

Serve/HTTPS 활성화 안내가 나오면 해당 Tailscale 계정의 관리자가 완료해야 합니다. 기존 443 서비스를 덮어쓰지 마세요. 대신 비어 있는 8443 포트를 쓰려면 `--https=8443`을 지정하고 출력된 포트 포함 주소로 접속합니다. Funnel로 인터넷에 공개하지 않습니다.

기존 접속 주소와 Tailscale 기기 이름은 설치·업데이트가 변경하지 않습니다. 대시보드 설정의 Spark 이름은 **화면 표시 이름**이며 주소나 운영체제 호스트명이 아닙니다.

SSH 포워딩을 사용하는 대안:

```bash
ssh -N -L 8767:127.0.0.1:8767 USER@SPARK_TAILSCALE_NAME
```

명령을 실행한 기기의 브라우저에서 <http://127.0.0.1:8767>을 엽니다. `USER`와 `SPARK_TAILSCALE_NAME`은 실제 값으로 바꿉니다.

## 4. 로그인·비밀번호 복구

설치 시 정한 비밀번호로 로그인합니다. 같은 브라우저·같은 접속 주소에서는 기간 제한 없이 유지하며, 서버 재시작과 업데이트에도 보존됩니다. 브라우저에는 비밀번호 대신 랜덤 세션키를, 서버에는 그 키의 해시만 저장합니다.

- 로그아웃, 비밀번호 재설정, 브라우저 데이터 삭제 시 다시 로그인합니다.
- 다른 브라우저, 다른 주소, 시크릿 창은 별도 저장 공간이므로 새 로그인이 필요할 수 있습니다.
- 최대 32개 세션을 보관하며 33번째 발급 시 가장 오래된 세션이 해제됩니다.

비밀번호를 잊으면 Spark의 로컬 OS 계정에서 트레이의 **비밀번호 재설정**을 선택하거나 다음을 실행합니다. 기존 웹 비밀번호는 필요하지 않습니다.

```bash
python3 ~/.local/share/dgx-spark-control-app/current/scripts/set-password.py
systemctl --user restart dgx-spark-control
```

기존 기기 로그인은 해제됩니다. 비밀번호, 유지관리 토큰, `password.json`, `sessions.json`은 GitHub나 공유 문서에 올리지 마세요.

## 5. 화면과 측정값

| 항목 | 표시 내용 |
|---|---|
| GPU | 사용률, 지원되는 SM 클럭 |
| CPU | 사용률, 코어별 상세, 읽을 수 있는 클럭 범위 |
| 통합 메모리 | OS 사용량·총량, 지원되는 메모리 클럭 |
| SSD | `/` 파일시스템 사용량·전체·사용자 가용·예약 여유 공간 |
| GPU 온도 | 드라이버가 제공하는 GPU 온도 |
| GPU 전력 | GPU 전력 센서 값. 전체 시스템 콘센트 전력이 아님 |
| 네트워크 | 물리 인터페이스의 수신·송신 MB/s. 인터넷 트래픽만 분리한 값이 아님 |
| 디스크 I/O | 물리 디스크 읽기·쓰기 MB/s |

카드를 누르면 실제 이력과 상세값이 표시됩니다. 미지원·준비 중 값은 `—`로 표시합니다. 메모리 설치 용량은 읽을 수 있는 펌웨어 정보에서 감지하고, 권한이 없으면 OS 총량임을 명시합니다. 128 GB로 고정하거나 임의로 반올림하지 않습니다. SSD의 전체 대비 사용률과 Linux `df` 사용률은 예약 공간 때문에 다를 수 있습니다.

설정에서 Spark 표시 이름을 저장하면 모든 접속 기기에 반영됩니다. 언어·화면 개인화는 브라우저별 설정입니다. 0.1.2는 화살표를 SVG로 표시하여 iOS의 이모지 대체를 피합니다.

## 6. 모델 관리 범위

0.1은 이미 설치된 **사용자 systemd 서비스**를 설정 파일에 등록한 경우에만 제어합니다. 모델 폴더 검색은 설정한 경로에서 후보를 찾으며, 자동 설치·삭제·등록은 하지 않습니다. 서비스 `active`는 실제 추론 준비 완료를 뜻하지 않습니다.

[모델 연동 가이드](MODELS.md)에 따라 기존 `config.json`을 백업하고 다른 필드를 보존한 채 `models`와 `model_roots`를 편집합니다. 예시는 실제 설치 경로와 서비스명으로 교체합니다.

```json
{
  "models": [
    {"id": "my-llm", "name": "My LLM", "engine": "llama.cpp", "service": "my-llm.service", "allow_control": true}
  ],
  "model_roots": ["/your/configured/models"]
}
```

위 내용으로 전체 설정 파일을 덮어쓰지 마세요. 파일을 수동 수정한 뒤 대시보드 서비스만 재시작합니다. 모델 자체의 설치와 추론 검증은 별도 작업입니다. 추론 tok/s·TTFT·요청 큐·모델 자동 교체는 후속 엔진 어댑터가 필요합니다.

## 7. 데스크톱 트레이와 자동 실행

GNOME 트레이는 대시보드 열기, Spark 이름 변경, 비밀번호 재설정, 서버 시작/재시작, 상태 확인을 제공합니다. GTK3/Python GI/Ayatana AppIndicator와 데스크톱 세션이 필요합니다. 필요한 패키지와 절차는 [데스크톱 가이드](DESKTOP.md)를 참고하세요. 트레이를 닫아도 웹 서버는 계속 실행됩니다.

의존성이 없다면 공식 Ubuntu 저장소의 패키지를 설치합니다. GNOME의 Ubuntu AppIndicators 확장도 활성화되어 있어야 합니다. 설치 프로그램은 이 시스템 설정을 자동 변경하지 않습니다.

```bash
sudo apt-get install --no-install-recommends python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
bash ~/.local/share/dgx-spark-control-app/current/scripts/start-tray.sh
```

재부팅 뒤 OS 로그인 전에도 서버를 실행하려면 관리자가 필요에 따라 다음을 한 번 설정합니다.

```bash
loginctl show-user "$USER" -p Linger
sudo loginctl enable-linger "$USER"
```

트레이 자체는 데스크톱 로그인 후 실행됩니다. 화면 없는 서버에서는 트레이 없이 웹 서비스를 사용할 수 있습니다.

## 8. 업데이트와 되돌리기

원하는 버전의 릴리스 노트를 확인한 다음 Spark에서 실행합니다.

```bash
bash ~/.local/share/dgx-spark-control-app/current/update.sh 0.1.2
```

공개 설치 파일 다운로드 → SHA256 검사 → 설치 → 인증된 상태 검사 순서입니다. 설정·비밀번호·기기 세션은 코드 밖에 저장되어 유지됩니다. 모델·드라이버를 교체하지 않습니다.

직전 코드 버전으로 복구:

```bash
bash ~/.local/share/dgx-spark-control-app/current/scripts/rollback.sh
```

0.1.1 ↔ 0.1.2는 동일한 설정 스키마를 사용합니다. 0.1.0은 비밀번호/트레이가 없던 버전이므로 복구 동작이 다릅니다. [상세 업데이트 정책](UPDATES.md)을 먼저 확인하세요.

## 9. 문제 확인과 자원 한도

```bash
systemctl --user status dgx-spark-control
journalctl --user -u dgx-spark-control -n 50
tailscale serve status
systemctl --user show dgx-spark-control.slice -p MemoryCurrent -p MemoryPeak -p MemoryMax
```

연결 실패 시 서버 상태, 접속 기기의 Tailscale 연결/접근 권한, Serve 주소 순서로 확인합니다. 옛 화면이 보이면 페이지를 새로고침합니다. 비밀번호 재설정 뒤에는 새 비밀번호로 로그인합니다.

서버+트레이 합산 상한은 **480 MiB = 503,316,480 bytes**, swap 0입니다. 브라우저·Tailscale·모델 엔진은 이 상한 밖에 있습니다. 접속 중 최대 5초 간격으로 결과를 공유하고, 접속 요청이 없으면 수집하지 않습니다. 단기 측정과 미검증 항목은 [버전별 검증 기록](releases/0.1.2.md)을 확인하세요.

## 10. 다른 LLM과 개발 이어가기

[AGENTS.md](../AGENTS.md) → [구조](ARCHITECTURE.md) → [모델 연동](MODELS.md) → [업데이트 정책](UPDATES.md) 순서로 읽게 합니다. 매 버전 VERSION·CHANGELOG·검증 기록·한국어/영어 가이드·GitHub Release·Notion 기록을 맞춥니다. 실제 비밀번호, 개인 모델 경로, 원시 로그를 공개 저장소에 넣지 않습니다.
