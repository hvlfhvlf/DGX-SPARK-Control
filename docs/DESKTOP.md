# Spark 데스크톱 트레이

0.1.1은 Spark GNOME 데스크톱 상단의 AppIndicator 트레이 메뉴를 제공한다. 서버와 분리된 작은 로컬 GUI 프로세스이며, 주기적으로 GPU나 파일을 수집하지 않는다.

메뉴: 대시보드 열기, Spark 표시 이름 변경, 비밀번호 재설정, 서버 시작/재시작, 상태, 트레이 닫기. 서버 재시작은 모델 서비스를 재시작하지 않는다. 설정 대화상자는 다른 창 위에 표시한다.

## 의존성과 자동 실행

서버 자체에는 외부 Python 의존성이 없다. 트레이는 Ubuntu의 GTK3, Python GI, Ayatana AppIndicator를 사용한다. 없는 경우 공식 Ubuntu 저장소에서:

```bash
sudo apt-get install --no-install-recommends python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
```

GNOME의 Ubuntu AppIndicators 확장이 활성화되어야 상단 트레이에 표시된다. 설치 프로그램은 시스템 패키지를 자동 설치하거나 데스크톱 확장 설정을 변경하지 않는다.

`~/.config/autostart/dgx-spark-control-tray.desktop`가 로그인 시 GUI 환경을 user systemd에 전달하고 `dgx-spark-control-tray.service`를 시작한다. 현재 그래픽 세션과 의존성이 확인되면 설치 직후에도 시작한다. 화면 없는 서버에서는 웹 서비스만 실행할 수 있다.

## 로컬 비밀번호 복구

Spark에 로그인한 OS 사용자 계정에서 트레이의 비밀번호 재설정을 열고 새 비밀번호를 두 번 입력한다. 기존 웹 비밀번호를 몰라도 된다. 완료 시 웹 세션을 해제하고 대시보드 서버만 다시 시작한다. 비밀번호 원문은 파일·로그에 저장하지 않는다.

트레이를 사용할 수 없을 때 Spark 터미널에서:

```bash
python3 ~/.local/share/dgx-spark-control-app/current/scripts/set-password.py
systemctl --user restart dgx-spark-control
```

비밀번호를 명령행 인자에 넣지 않는다. 로컬 OS 계정 접근 권한이 복구 권한이다. 원격 웹 화면에서는 비밀번호 없이 재설정할 수 없다.

## 메모리 한도

`dgx-spark-control.slice`에 서버와 트레이를 함께 넣어 합산 480 MiB (503,316,480 bytes)로 제한한다. 트레이 단독 상한은 128 MiB이며 전체 상한이 우선한다. 웹 브라우저와 모델 엔진은 이 그룹 밖에서 실행한다. 트레이를 닫아도 서버는 계속 동작한다.

```bash
systemctl --user status dgx-spark-control-tray
systemctl --user show dgx-spark-control.slice -p MemoryCurrent -p MemoryPeak -p MemoryMax
journalctl --user -u dgx-spark-control-tray -n 30
```

제거 시 서버와 트레이 서비스를 모두 중지하고 autostart 파일도 제거한다. 비밀번호·개인 설정 디렉터리는 사용자가 명시적으로 삭제하기 전까지 보존한다.
