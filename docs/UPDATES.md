# 버전 관리 / Updates

소스 저장소: https://github.com/hvlfhvlf/DGX-SPARK-Control

버전은 `0.1.0`처럼 SemVer, Git tag는 `v0.1.0`. 버전별 tar.gz와 SHA256SUMS를 GitHub Releases에 함께 게시한다. 코드와 개인 설정 디렉터리는 분리되어 있다.

## 사용자 업데이트

원하는 버전의 변경점과 데이터 스키마 호환성을 읽은 뒤:

```bash
bash ~/.local/share/dgx-spark-control-app/current/update.sh X.Y.Z
```

공식 저장소에서 해당 버전 archive/checksum 다운로드 → SHA256 비교 → 경로/링크가 안전한 archive인지 확인 → staging → 문법 확인 → 설정 백업 → current 링크 교체 → 재시작 → 인증된 healthcheck 순서이다. healthcheck 실패 시 이전 코드로 복원한다. 업데이트는 명시적으로 실행하며 상시 자동 갱신하지 않는다.

## 되돌리기

```bash
bash ~/.local/share/dgx-spark-control-app/current/scripts/rollback.sh
```

0.1의 config schema 1에서는 설정·토큰을 유지한 코드 rollback이다. 미래에 schema가 바뀌면 역방향 호환성을 문서화하고 백업 데이터 복원/마이그레이션을 구현하기 전에는 새 버전을 배포하지 않는다. `config.json` 백업에는 개인 경로가 있을 수 있으므로 외부 공유하지 않는다.

0.1.1부터 비밀번호·기기 세션·하드웨어 정보도 코드 외부에 보관한다. 정상 재시작과 업데이트는 로그인을 해제하지 않는다. 0.1.0으로 되돌리면 그 버전은 비밀번호 로그인과 트레이를 지원하지 않아 기존 로컬 access-token 방식으로 돌아간다. 비밀번호 해시 파일은 삭제하지 않으며 0.1.1로 다시 올리면 적용된다. 세션 유지가 필요하면 0.1.1 이상끼리 복구한다.

## 개발 릴리스 체크리스트

1. 요구사항과 구현 범위를 확인하고 README·API 계약·LLM 가이드를 갱신.
2. VERSION, CHANGELOG.md, docs/releases/<version>.md 갱신. 실제 수행/미수행을 구분.
3. Linux 단위/API 테스트, UI desktop/mobile, 설치·업데이트·rollback·설정 보존, cgroup 메모리 측정.
4. Spark에서 모델을 켜거나 끄지 않고 기본 검증. 실제 제어는 전용 테스트 서비스로 먼저 확인.
5. `python3 scripts/package.py` → 깨끗한 디렉터리에 추출 → 테스트 재실행.
6. 소스 commit과 동일한 버전 tag를 push. tar.gz와 SHA256SUMS 업로드, 릴리스 노트 작성.
7. GitHub에서 다운로드한 실제 asset checksum/설치 확인.
8. Notion DGX 프로젝트에 해당 버전 링크·commit·구조·변경점·검증/제약 갱신.

GitHub 로그인/권한 토큰, Spark access-token, 실측 raw 로그와 모델 프롬프트는 릴리스에 넣지 않는다. 웹의 버튼으로 자동 업데이트하는 기능은 0.1 범위에 없다. 설치용 스크립트가 명시적 버전 업데이트를 담당한다.
