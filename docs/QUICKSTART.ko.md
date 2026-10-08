# DGX Spark 간편 설치 — 한국어

**0.2.0 · Ubuntu 24.04 / ARM64** · [English](QUICKSTART.en.md)

## 1. 설치 파일 받기

[GitHub 릴리스](https://github.com/hvlfhvlf/DGX-SPARK-Control/releases/tag/v0.2.0)에서 **dgx-spark-control_0.2.0_arm64.deb**를 Spark에 다운로드하세요.

파일을 열어 소프트웨어 설치 앱에서 **설치**를 누릅니다. 관리자 인증이 나올 수 있습니다. 필요한 GTK·트레이 패키지는 Ubuntu 저장소에서 설치됩니다. 인터넷 연결이 필요하며, 모델·CUDA·NVIDIA 드라이버는 교체하지 않습니다.

파일을 열 설치 앱이 없거나 터미널을 선호하면 다운로드 폴더에서 실행하세요:

```bash
sudo apt install ./dgx-spark-control_0.2.0_arm64.deb
```

`apt` 명령의 `./`를 포함하세요. 파일이 다른 폴더에 있다면 해당 폴더로 먼저 이동하세요. 아래 초기 설정은 **sudo 없이 일반 사용자로** 실행합니다.

## 2. 초기 설정 열기

Spark 앱 목록에서 **DGX-SPARK-Control 초기 설정**을 검색해 엽니다. 또는:

```bash
dgx-spark-control setup
```

**언어 선택 → Spark 표시 이름·비밀번호 → 연결 확인 → 저장하고 시작** 순서입니다.

- 새 설치: 비밀번호를 두 번 입력합니다. 입력한 문자는 숨겨집니다.
- 기존 설치: 이름은 미리 표시됩니다. 비밀번호 두 칸을 비워두면 기존 비밀번호와 기기 로그인을 유지합니다.
- 비밀번호를 변경하면 기존 기기의 로그인이 해제됩니다.
- 완료 후 **대시보드 열기** 또는 **주소 복사**를 누릅니다.
- 창을 닫아도 서버가 계속 실행됩니다. 설정 마법사는 상주하지 않습니다.

## 3. 다른 기기에서 접속하기

Spark 자체에서는 **http://127.0.0.1:8767**로 접속합니다. 이 로컬 주소를 휴대폰에 입력하면 Spark로 연결되지 않습니다.

다른 기기에서는 Spark의 **Tailscale HTTPS 주소**를 사용합니다. 기존 연결은 자동 감지하며, 마법사와 트레이에서 복사할 수 있습니다. Spark와 접속 기기가 접근 허용된 동일 Tailscale 네트워크에 연결되어 있어야 합니다.

Tailscale이 없으면 [공식 Linux 설치 안내](https://tailscale.com/download/linux)에 따라 설치하고 로그인하세요. 초기 설정 완료 후 Spark 터미널에서 먼저 확인합니다:

```bash
tailscale serve status
```

기존 연결이 있다면 유지합니다. **HTTPS 443 포트가 비어 있을 때만** 아래를 실행하세요:

```bash
sudo tailscale serve --bg --https=443 http://127.0.0.1:8767
tailscale serve status
```

계정의 HTTPS/Serve 활성화 안내가 나오면 브라우저에서 완료합니다. 443이 다른 서비스에 사용 중이면 비어 있는 8443을 사용하고 출력된 포트 포함 주소로 접속하세요. **Funnel은 켜지 않습니다.** 설치 프로그램은 Tailscale 로그인·승인을 대신하거나 기존 연결을 변경하지 않습니다.

## 4. 트레이와 자동 실행

트레이: 대시보드 열기, 주소 복사, 초기 설정, 업데이트 확인, 이름 변경, 비밀번호 재설정, 서버 시작·재시작, 상태, 트레이 닫기.

- **업데이트 확인**은 GitHub 릴리스 페이지를 엽니다. 자동 설치하거나 주기적으로 확인하지 않습니다.
- 트레이가 없으면 GNOME 확장에서 **Ubuntu AppIndicators**를 켜세요. 브라우저 기능은 사용할 수 있습니다.
- 서버는 사용자 서비스로 등록됩니다. OS 로그인 전에 서버를 시작하려면 관리자가 한 번 실행합니다:

```bash
sudo loginctl enable-linger "$USER"
```

트레이는 데스크톱 로그인 후 시작됩니다. 비밀번호를 잊으면 트레이의 **비밀번호 재설정**을 사용하세요. 기존 웹 비밀번호 없이 로컬 OS 계정 권한으로 재설정할 수 있습니다.

## 5. 업데이트·삭제

새 버전의 `.deb`를 다운로드하고 같은 방식으로 설치하세요. 로그인한 사용자 중 패키지 관리가 활성화된 대시보드는 다시 시작합니다. 로그아웃 상태에서는 다음 사용자 서비스 시작에 새 코드가 적용됩니다. Spark 이름, 비밀번호, 기기 로그인, 모델 등록은 유지됩니다.

패키지 설치판에 예전 `update.sh`나 `rollback.sh`를 혼용하지 마세요. 실패 복구와 압축 설치판에서의 이전은 [업데이트 가이드](UPDATES.md)를 참고하세요.

삭제:

```bash
sudo apt remove dgx-spark-control
```

활성 사용자 대시보드를 중지하고 프로그램 파일을 제거합니다. 사용자 설정·비밀번호·로그인 데이터와 기존 압축판 코드 백업은 보존합니다. 삭제 당시 로그아웃한 사용자의 등록 흔적도 남을 수 있으며, 실행 파일이 없으면 서버는 시작되지 않습니다. 모델·드라이버·Tailscale은 삭제하지 않습니다.

## 6. SSH·LLM 설치

LLM에는 이 문서와 [AGENTS.md](../AGENTS.md)를 읽게 하세요. 터미널/SSH 권한이 필요합니다.

```bash
dgx-spark-control setup --check
dgx-spark-control setup --cli --lang ko
```

`--check`는 설정을 변경하지 않는 JSON 점검입니다. 새 설치의 비밀번호는 대화형 터미널에서 입력하세요. 비밀번호를 명령줄 인자, 채팅, 로그에 넣지 마세요.

**기존 비밀번호가 있는 설치만** 입력 없이 이전·적용할 수 있습니다:

```bash
dgx-spark-control setup --non-interactive
```

새 설치에서 이 명령은 종료 코드 2와 `setup_required`를 반환하고 서버를 시작하지 않습니다. Tailscale 승인과 관리자 인증이 필요하면 사용자가 완료합니다.

## 문제 확인

```bash
systemctl --user status dgx-spark-control
journalctl --user -u dgx-spark-control -n 50
tailscale serve status
systemctl --user show dgx-spark-control.slice -p MemoryCurrent -p MemoryMax
```

서버+트레이 상한은 **480 MiB**입니다. 설치 창, 브라우저, 모델과 Tailscale의 메모리는 별도입니다. 이번 버전은 DGX Spark Ubuntu ARM64 대상이며 Windows·다른 플랫폼 확장은 보류합니다.

[전체 사용자 가이드](GUIDE.ko.md) · [검증 기록과 한계](releases/0.2.0.md)
