# Desktop tray / Spark 데스크톱 트레이 — 0.2.0

The GTK3/Ayatana AppIndicator tray is a separate, small process. It does not poll metrics. GTK is also used for the on-demand setup wizard; there is no embedded browser or resident installer.

Menu / 메뉴:

- Open dashboard / 대시보드 열기
- Copy connection address / 접속 주소 복사
- Setup / 초기 설정
- Check for updates / 업데이트 확인
- Change Spark name / 이름 변경
- Reset password / 비밀번호 재설정
- Start / Restart / Status — 서버 시작 / 재시작 / 상태
- Close tray / 트레이 닫기

The address action detects a Tailscale root proxy to this dashboard, without changing it. Otherwise it copies the local-only URL and explains that limitation. Update checking opens the GitHub release page. The server remains running when the tray closes, and dashboard restarts do not restart models.

## Setup and dependencies / 초기 설정과 의존성

The `.deb` declares Python GI, GTK3 and Ayatana dependencies, which apt resolves from Ubuntu. GNOME's Ubuntu AppIndicators extension must also be enabled; setup does not change extension settings. A desktop session is needed for the tray, but not the server.

```bash
dgx-spark-control setup
dgx-spark-control start-tray
```

For archive installs only, install missing GTK packages and run the archive's tray launcher:

```bash
sudo apt-get install --no-install-recommends python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1
bash ~/.local/share/dgx-spark-control-app/current/scripts/start-tray.sh
```

The tray starts after desktop login. Optional `sudo loginctl enable-linger "$USER"` lets the server start before login; it does not create a desktop tray before a desktop session exists.

## Password recovery / 비밀번호 복구

Use Reset password from the local tray and enter a new password twice. The old password is not required; the local OS account grants recovery authority. Prior web sessions are revoked. For package installations without a tray:

```bash
python3 /usr/lib/dgx-spark-control/scripts/set-password.py
systemctl --user restart dgx-spark-control
```

Archive users use the corresponding script under their app's `current/scripts`. Never put a password in command-line arguments. 원격 웹 인증 없이 비밀번호를 재설정하는 기능은 제공하지 않습니다.

## Resource checks / 자원 확인

Server + tray share `dgx-spark-control.slice`, capped at 480 MiB with no swap. The tray alone is capped at 128 MiB. Setup and browsers are transient desktop apps outside that slice. No persistent setup/update agent is added.

```bash
systemctl --user status dgx-spark-control-tray
systemctl --user show dgx-spark-control.slice -p MemoryCurrent -p MemoryPeak -p MemoryMax
journalctl --user -u dgx-spark-control-tray -n 30
```

[한국어 설치 안내](QUICKSTART.ko.md) · [English installation](QUICKSTART.en.md)
