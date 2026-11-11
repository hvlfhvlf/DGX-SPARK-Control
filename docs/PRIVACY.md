# Privacy and release contents / 개인정보와 배포 범위

## What stays on Spark / Spark에 남는 정보

- Password hashes, session hashes, maintenance tokens, Spark display name and service registry stay in the user data directory, outside package-managed code. Password plaintext is not stored. Browser sessions stay in that browser until logout/reset/removal; they are not sent to GitHub.
- Service app addresses, execution bindings and private model paths belong to each installation. The public example is generic; a fresh installation starts without personal service registrations.
- The browser receives authenticated readings and selected display metadata from its Spark. Service probes use fixed API paths on loopback, or an OS-verified listening IPv4 address belonging to the same Spark when loopback refuses the connection. They do not accept a remote API host. Raw prompts, workflows and service logs are not forwarded by the dashboard.

비밀번호 해시·로그인·유지관리 토큰·표시 이름·서비스 주소와 경로는 Spark의 개인 데이터 디렉터리에 보관합니다. 패키지에는 실사용 설정·키·로그·모델 파일이 없습니다. 대시보드의 API 구현과 일반 예제는 공개되지만 실제 비밀값은 포함하지 않습니다.

## Network behavior / 통신

The installed browser requests its own Spark API. Fonts are self-hosted. The dashboard has no analytics, automatic telemetry upload or remote update agent. The tray dashboard-update menu opens GitHub only when selected. Explicit application update checks contact fixed official GitHub/npm sources; approved installs fetch their official artifacts/dependencies using the existing app toolchain. This is not telemetry upload. Tailscale communicates independently and follows the operator's network policy. Opening an app or documentation follows the selected destination and that app's own privacy/authentication rules.

사용 통계·측정값을 외부로 자동 전송하는 기능은 없습니다. 트레이의 대시보드 업데이트 메뉴는 GitHub 페이지를 엽니다. 상세창에서 명시적으로 앱 업데이트를 확인하면 지정된 공식 GitHub/npm 소스에 접속하며, 적용 시 공식 파일과 의존성을 받습니다. 측정값·대화 내용을 업로드하지 않습니다. 앱 열기와 외부 문서 링크는 사용자가 선택한 서비스로 연결합니다. Tailscale의 통신은 대시보드와 별도이며 기존 접근 정책을 따릅니다.

## Release review / 공개 전 검사

Review the Git source/history and final archive/package bytes for recognizable secret patterns, known local credentials/identifiers, private configuration filenames and personal archive owners. Build from the tagged Git tree, distribute SHA256SUMS and verify downloads. Tests contain clearly synthetic credentials and loopback example URLs, not production keys. No personal ComfyUI gateway, Tailscale IP/domain, SSH configuration, prompts or screenshots are bundled.

이번 검사는 알려진 실제 비밀값 대조, 키 패턴·개인 경로·기기 식별자·금지 파일·패키지 소유자 메타데이터 검사와 통신 코드 검토를 포함합니다. 패턴 검사가 모든 형태의 비밀정보 부재를 수학적으로 보증하지는 않습니다. 설정·로그를 이슈에 붙이기 전에는 별도로 검토하세요. 검증 범위는 [릴리스 기록](releases/0.3.4.md)에 정리합니다.

Harness Open App reads a bounded local startup log only on explicit authenticated request and hands the current authentication URL to that browser. The URL is not added to the registry, activity history or release files. Treat copied launch URLs as credentials. Application update bindings, state and backups also remain private on Spark.

Harness 앱 열기는 인증된 요청 시 제한된 로컬 시작 로그에서 현재 인증 주소를 얻어 해당 브라우저로 전달합니다. 주소를 서비스 등록·활동 이력·배포 파일에 저장하지 않습니다. 복사한 인증 주소는 비밀정보로 취급하세요. 업데이트 연결·상태·백업도 Spark에 비공개로 남습니다.
