# 설치 / Installation — 0.1.0

## 지원 범위

- NVIDIA DGX Spark, Ubuntu 24.04, ARM64, Python 3.12+, user systemd, cgroup v2.
- 기타 Linux는 CPU/메모리 읽기가 가능할 수 있으나 검증 대상과 구분한다. Windows는 서버 설치 대상이 아니다.
- 기존 모델, CUDA, 드라이버, Docker, Tailscale 설치를 변경하지 않는다. 기본 포트 8767.

## 설치

README의 GitHub Release 다운로드 → SHA256 확인 → 빈 디렉터리 압축 해제 → `bash install.sh` 순서로 진행한다. 일반 사용자 계정으로 실행하며 sudo 설치를 요구하지 않는다.

파일 배치:

| 위치 | 역할 |
|---|---|
| `~/.local/share/dgx-spark-control-app/releases/` | 버전별 실행 코드 |
| `~/.local/share/dgx-spark-control-app/current` | 현재 실행 버전 링크 |
| `~/.local/share/dgx-spark-control-app/previous` | 이전 버전 링크 |
| `~/.local/share/dgx-spark-control/config.json` | 이름·모델 등록·검색 경로 |
| `~/.local/share/dgx-spark-control/access-token` | 비공개 접속 토큰, 0600 |
| `~/.config/systemd/user/dgx-spark-control.service` | 서버 자동 실행·자원 한도 |

## 접속

Spark 브라우저에서 http://127.0.0.1:8767 접속. 로컬 터미널에서 `cat ~/.local/share/dgx-spark-control/access-token`으로 읽은 토큰을 화면에 입력한다. 토큰은 브라우저 탭의 sessionStorage에만 보관한다. 설정·실측값·모델 제어 API는 모두 인증이 필요하다.

다른 기기에서 SSH 포워딩:

```bash
ssh -N -L 8767:127.0.0.1:8767 USER@SPARK_TAILSCALE_NAME
```

그 기기에서 http://127.0.0.1:8767을 연다.

Tailscale HTTPS 사용 시 먼저 `tailscale serve status`로 기존 라우팅을 확인한다. 이미 사용 중인 Serve 포트/경로를 덮어쓰지 않는다. 예를 들어 비어 있는 8443 포트에:

```bash
tailscale serve --bg --https=8443 http://127.0.0.1:8767
tailscale serve status
```

출력된 실제 HTTPS 주소를 사용한다. 필요한 경우 관리자가 해당 명령을 승인한다. **Funnel/public exposure는 설정하지 않는다.** Tailscale 접근 제어와 대시보드 토큰을 함께 사용한다. 실제 모델 제어판을 공개 디자인 미리보기 호스팅에 배포하지 않는다.

재부팅 후 로그인 없이 실행하려면 기존 `loginctl show-user "$USER" -p Linger`를 확인하고, 필요할 때 관리자가 `sudo loginctl enable-linger "$USER"`를 실행한다. 설치 프로그램은 이 시스템 설정을 임의 변경하지 않는다.

## 상태·중지·제거

```bash
systemctl --user status dgx-spark-control
journalctl --user -u dgx-spark-control -n 50
systemctl --user stop dgx-spark-control
```

제거는 먼저 `systemctl --user disable --now dgx-spark-control`로 중단한 뒤 앱 디렉터리와 unit 파일만 제거한다. 개인 설정과 토큰 디렉터리는 보존한다. Tailscale Serve를 추가했다면 해당 포트만 해제한다. 다른 Serve 설정과 모델 서비스는 건드리지 않는다.
