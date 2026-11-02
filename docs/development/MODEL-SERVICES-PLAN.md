# 모델 탭: 서비스 제어와 실행 프로필 설계

상태: 2026-11-02 원 설계 및 비교 조사. 0.3.0~rc1에서 1차 구현을 진행했으며 정확한 현재 계약은 ../MODELS.md와 ../releases/0.3.0~rc1.md를 따른다. 아래 장기 목표 전체가 구현된 것은 아니다. 특히 자동 교체/rollback, secret_ref, 엔진 load/unload, 로그 보기, Docker/직접 프로세스 관리, 웹 실행 설정 편집은 보류다. 현재 구현은 전역 작업 1개, 정지 후 프로필 선택, 조회 전용 후보 등록으로 범위를 좁혔다. GitHub 게시 보류. 개인 호스트명·주소·경로·인증 정보는 제외한다.

## 1. 구현 전 기준 코드와 실기기에서 확인한 것

- 현재 models.py에는 허용 목록에 등록된 사용자 systemd 서비스의 시작·정지 기능이 있다. 상태는 is-active, 변경 요청은 --no-block이며 명령 접수와 준비 완료가 구분돼야 한다.
- 실제 설치의 등록 목록과 모델 검색 경로는 모두 비어 있다. 서비스들이 설치되어 있어도 모델 탭에 자동 등록되지 않은 상태다.
- 점검 시점에 ComfyUI 앱과 연결용 보조 서비스, Hermes Gateway가 실행 중이었다. Qwen/TensorFold 추론 서비스와 별도 Gemma 서비스는 설치되어 있지만 중지 상태였다. 실행 상태는 관측 시점 값이며 추론 성공 검증이 아니다.
- ComfyUI의 보조 연결 서비스는 기존 Wants/PartOf 관계가 있다. 하나의 앱 카드에서 이 관계를 설명하되 기존 unit 파일을 덮어쓰거나 보조 서비스를 독립 모델처럼 표시하지 않는다.
- Hermes가 현재 어떤 모델 공급자를 사용하는지는 이번 조사에서 검증하지 않았다. Qwen에 의존한다고 자동 연결하지 않는다.
- 대시보드+트레이 cgroup 관측값은 57,708,544 bytes(약 55.0 MiB), 상한 480 MiB였다. 이것은 현재 프로그램 관측값이며 새 모델 제어 구현이나 타 대시보드의 부담 측정 결과가 아니다.

## 2. 다른 대시보드에서 참고한 구조

소스 열람만 수행했다. 비교 제품을 Spark에 설치·실행하거나 벤치마크하지 않았다.

| 대상 | 확인한 작동 방식 | 우리 설계에 반영 |
| --- | --- | --- |
| MiaAI-Lab sparkDash | React/Vite 화면 + Node/Express/WebSocket. 로컬 또는 SSH 수집. 모델별 디렉터리·start/stop 스크립트를 JSON으로 등록. LauncherManager는 작업 상태와 로그를 관리하고 명령 빌더는 분리 세션/PID·시작 시각을 추적한다. LLM/ComfyUI/Hermes용 검사기가 분리돼 있다. | UI 코드와 등록 정보 분리, 엔진별 검사기, 실행 진행 상태, 제한된 로그. 우리 설치에서는 기존 systemd를 사용하고 새 스크립트/PID 감독기를 중복 구현하지 않는다. |
| paul-aviles NVIDIA-DGX-Spark-Dashboard | 별도 호스트의 FastAPI/AsyncSSH가 Spark 두 대에 묶음 명령을 보내고 WebSocket으로 표시. 해당 리비전은 각 WebSocket 핸들러에 1초 수집 루프가 있다. | 묶음 조회를 참고한다. 기기별/브라우저별 중복 수집 대신 서버 캐시를 공유한다. 이 저장소는 주로 모니터링이며 모델 제어 레지스트리의 근거로 삼지 않는다. |
| NVIDIA 기본 DGX Dashboard | 공식 문서상 시스템 상태·업데이트·설정·JupyterLab을 제공한다. JupyterLab 작업 디렉터리별 환경 및 사용자별 포트 관리. | 앱 실행과 접속 경로를 분리한다. 범용 모델 자동 등록 기능이 있다고 확대 해석하지 않는다. |

MIA 소스 기준: 51daebb6aaecfd3dfaeb2ef9055e867024c84c84.
- [LauncherStore](https://github.com/MiaAI-Lab/sparkDash/blob/51daebb6aaecfd3dfaeb2ef9055e867024c84c84/server/llmlaunch/LauncherStore.js): 등록 정보 영속화.
- [LauncherManager](https://github.com/MiaAI-Lab/sparkDash/blob/51daebb6aaecfd3dfaeb2ef9055e867024c84c84/server/llmlaunch/LauncherManager.js), [commands](https://github.com/MiaAI-Lab/sparkDash/blob/51daebb6aaecfd3dfaeb2ef9055e867024c84c84/server/llmlaunch/commands.js), [validation](https://github.com/MiaAI-Lab/sparkDash/blob/51daebb6aaecfd3dfaeb2ef9055e867024c84c84/server/llmlaunch/validate.js): 로컬/SSH 실행, 입력·경로 검사, 상태/로그.
- [LlmProbe](https://github.com/MiaAI-Lab/sparkDash/blob/51daebb6aaecfd3dfaeb2ef9055e867024c84c84/server/collectors/LlmProbe.js), [ComfyProbe](https://github.com/MiaAI-Lab/sparkDash/blob/51daebb6aaecfd3dfaeb2ef9055e867024c84c84/server/collectors/ComfyProbe.js), [HermesProbe](https://github.com/MiaAI-Lab/sparkDash/blob/51daebb6aaecfd3dfaeb2ef9055e867024c84c84/server/collectors/HermesProbe.js): 엔진별 API/CLI 확인. 자동 API 탐지와 안전한 시작 명령 생성은 서로 다른 문제다.
- [config](https://github.com/MiaAI-Lab/sparkDash/blob/51daebb6aaecfd3dfaeb2ef9055e867024c84c84/server/config.js): 빠른 수집 기본값 2초, 저장소 5초, Hermes 600초 등 도메인별 주기. 코드 규모나 프레임워크만으로 실제 RAM 사용량을 단정하지 않는다.

다른 비교 근거:
- [community server.py](https://github.com/paul-aviles/NVIDIA-DGX-Spark-Dashboard/blob/72d6e6acc143aa2f721ac52b5be8a0a367f89938/backend/server.py): ws_endpoint 내부 수집 루프와 SSH 연결.
- [NVIDIA 공식 DGX Dashboard 안내](https://docs.nvidia.com/dgx/dgx-spark/dgx-dashboard.html).
- 비교 대상의 소스·UI 자산을 복사하지 않고 설계 패턴을 참고한다.

## 3. 사용자에게 보이는 구조

탭은 **모델 / Models**로 유지하고 페이지 제목은 **서비스와 모델 / Services & models**로 한다.

상단: 전체 / 실행 중 / 중지됨 / 주의 필터, [서비스 찾기], [추가].
본문: ComfyUI, LLM 서버(현재 선택 모델 Qwen), Hermes Gateway 카드.
하단: 설치 모델 목록을 별도 접기 영역으로 둔다. 체크포인트 파일 수십 개가 서비스 카드와 섞이지 않게 한다.

카드에는 다음 순서만 기본 노출한다.
1. 이름, 앱/추론/에이전트 종류, 상태 배지.
2. 현재 실행 프로필 또는 실제 로드 모델. 미확인은 “확인 안 됨”.
3. 관련 핵심값 두 개: ComfyUI 진행·대기 수, LLM 로드 모델·준비 상태, Hermes Gateway 상태·연결 공급자. 지원하지 않는 값은 숨기거나 조회 불가로 표시.
4. [켜기/끄기]와 [열기] 또는 [상세]. 프로필 변경·재시작·자동 시작·등록 해제는 상세/더보기.

상세창: 상태/동작, 프로필, 연결 관계, 최근 작업 결과 순서. 명령줄·경로·원시 로그는 접기 영역. 이전 지표 상세창의 정돈된 구성과 현재 폰트를 유지한다.

PC는 2~3열, 폰은 최소 2열의 짧은 요약 카드. 긴 이름은 최대 두 줄, 중요 수치는 고정 영역. 폰 카드에서는 버튼 두 개만 노출하고 나머지는 상세창에 둔다. 320/390px에서 상태·버튼 잘림 없이 검증한다. 모달 모션 300/200ms, 호버 200ms 유지. 카드 전체를 실행 버튼으로 사용하지 않는다.

## 4. 서비스 / 실행 프로필 / 설치 모델을 분리

- **Service**: 사용자가 켜고 끄는 논리적 앱 또는 추론 서버. 이름·종류·어댑터·프로필 목록을 가진다. ID는 모델 표시명을 바꿔도 유지한다.
- **Profile**: 그 서비스를 실행하는 검증된 설정 묶음. 기존 사용자 unit, 모델 참조, 점검용 endpoint, 시작 제한시간, 동일 포트/자원 충돌 그룹을 지정한다.
- **Asset**: 디스크에 있는 모델 또는 확인된 외부 공급자 모델 참조. 존재 여부·메타데이터 출처를 관리한다. 파일이 발견됐다는 것과 실행 가능/로드 완료는 다르다.
- **Observation / Operation**: 실제 관측과 진행 중 작업. 설정 파일의 desired/default 값을 실제 실행 상태로 표시하지 않는다.

초기 단계는 프로필 하나당 이미 설치된 사용자 systemd unit 하나에 연결한다. 같은 논리 서비스의 프로필 둘이 서로 다른 unit을 가리켜도 한 번에 하나만 시작한다. 기존 스크립트형 설치는 로컬 설치 작업에서 user unit으로 감싼 뒤 등록한다.

ComfyUI 체크포인트 변경은 워크플로의 책임이다. 서버 프로필 변경과 워크플로 내 모델 변경을 동일한 “교체” 버튼으로 취급하지 않는다.
Hermes 공급자 모델 선택은 Hermes 설정의 책임이다. 대시보드의 추론 서버 프로필을 바꿨다고 Hermes 설정을 자동 수정하지 않는다.

[선언형 레지스트리 예시](SERVICE-REGISTRY.example.json)는 **제안 형식**이며 현재 앱은 읽지 않는다.

## 5. 실행 계층

브라우저 → 현재 인증 API → 서비스 레지스트리/작업 관리자 → 고정 manager(systemd-user) → 기존 서비스.
같은 API 내부의 엔진 어댑터가 등록된 로컬 endpoint/허용된 상태 파일에서 준비 상태와 관련 지표를 읽는다.

LLM 에이전트나 별도 수집 데몬을 상주시킬 필요가 없다. 브라우저는 service_id/profile_id/action만 전달한다. shell 문자열·실행 파일 경로·임의 Python 모듈·sudo 암호를 웹 요청에서 받아 실행하지 않는다. 어댑터는 제품 코드의 고정 목록에서 선택한다.

단일 Python 프로세스를 유지하되 긴 시작 대기는 HTTP 요청에 묶지 않는다. 202 + operation_id를 반환하고 최대 2개 작업 worker, 자원 그룹별 잠금, 최대 200개 작업 기록을 둔다. 명령 접수는 성공 완료가 아니다. 작업은 시작 명령 → 프로세스 확인 → 준비 확인 → 완료/실패/시간 초과로 끝난다.

대시보드 재시작 시 진행 작업을 성공/실패로 추측하지 않는다. 마지막 operation 메타데이터와 systemd 상태를 대조해 확인 중/결과 불명으로 복구한다. start/stop을 자동 재실행하지 않는다.

## 6. 실제 상태와 준비 여부

두 값을 별도로 저장한다.
- process_state: stopped / starting / running / stopping / failed / unknown.
- readiness: ready / loading / degraded / unreachable / unsupported / unknown.

화면에서는 “준비 완료”, “실행 중 · 준비 미확인”, “시작 중”, “중지 중”, “오류”, “연결 끊김”처럼 조합한다. 마지막 관측 시각을 보이고 stale을 중지됨이나 정상으로 바꾸지 않는다.

어댑터 공통 계약:
- observe(): 관측 시각, 프로세스 상태, readiness, 실제 모델 식별, 지원 기능.
- busy(): 현재 작업 있음/없음/모름. 모름은 0이 아니다.
- capabilities: status, readiness, model_identity, queue, metrics, logs, drain, reload_model 등을 설치 버전에 맞춰 판정.
- process start/stop은 manager의 책임. 모델 load/unload는 지원 엔진 어댑터의 별도 기능이다.

| 엔진/앱 | 첫 연결 방식 | 제한 |
| --- | --- | --- |
| ComfyUI | 기존 unit + /system_stats 및 /queue의 제한된 조회 | /queue 응답에 워크플로가 포함될 수 있으므로 크기 상한 후 건수만 추출; 프롬프트는 저장/전달하지 않음. 작업 취소와 서버 정지는 별도. |
| Qwen/TensorFold | 기존 unit + 설치 서버의 검증된 API 계약 | Qwen은 모델 이름이며 vLLM이라고 추정하지 않음. 실제 TensorFold 버전·모델 ID·health/metrics 의미 검증 후 기능 활성화. |
| Hermes Gateway | 기존 unit + 설치 버전이 제공하는 상태 신호 | running만으로 공급자/메시징 연결 정상 판정 금지. 지원되는 경우에만 drain 사용; 최신 문서의 명령을 구버전에 그대로 적용하지 않음. |
| vLLM / llama.cpp | 후속 어댑터, unit 제어 공통 사용 | /v1/models 응답만으로 엔진 종류나 추론 준비를 확정하지 않음. 모델 ID·sleep/loading 상태 등을 해당 버전 계약으로 확인. |
| LM Studio / Ollama | 후속 어댑터에서 서버 시작과 모델 load/unload 분리 | 서버가 켜져 있어도 모델은 미로드일 수 있음. 지원 OS/런타임을 별도로 검증하며 다른 플랫폼 확장은 계속 보류. |
| Docker 설치 | 초기에는 검증된 user unit이 컨테이너 명령을 감싸는 방식 | 웹 서버에 Docker socket 또는 일반 명령 실행 권한을 직접 부여하지 않음. |

공식 근거: [ComfyUI routes](https://docs.comfy.org/development/comfyui-server/comms_routes), [vLLM serving](https://docs.vllm.ai/en/latest/serving/online_serving/), [Hermes gateway](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/messaging/index.md), [LM Studio load API](https://lmstudio.ai/docs/developer/rest/load).
vLLM의 일부 sleep/checkpoint 상태에서는 health가 200이어도 요청 수락 상태가 다를 수 있다. 단순 HTTP 200을 모든 엔진의 추론 준비 판정으로 재사용하지 않는다.

## 7. 켜기·끄기·프로필 교체

켜기: 프로필 유효성/파일 존재/등록 unit/포트/작업 잠금 확인 → 시작 → 준비 상태 확인.
끄기: 영향 받는 실제 서비스·보조 unit·진행 작업을 표시 → 정지 요청 → 프로세스 종료 확인.
- 지원하면 drain을 제공하되 작업량을 모르면 “진행 작업 확인 불가”로 표시한다.
- 메모리가 모자라다고 ComfyUI나 다른 모델을 임의 종료하지 않는다.
- 등록된 의존 서비스가 실행 중이면 영향과 선택지를 보여준다. Hermes가 해당 Qwen을 쓰는 것으로 확인된 경우에만 연관 경고한다.
- 자동 시작은 현재 실행 상태와 별개이다. 기존 enabled/disabled를 보존하고 명시적으로 변경할 때만 적용한다.

프로필 교체는 2단계다.
1. 새 설정을 검증·저장한다. 실행 중 서비스는 유지한다. “저장됨, 미적용” 상태.
2. 명시적인 적용에서 이전 설정/상태 기록 → 작업 상태 확인 → 이전 unit 정지 완료 → 새 unit 시작/준비 확인.
같은 포트를 쓰는 두 서버를 동시에 시작하지 않는다. 실패하면 이번 작업이 시작한 대상만 정리한다. 이전에 실행 중이었던 프로필은 사전에 선택한 복구 정책에 따라 한 번만 재시작·확인한다. 복구 실패도 별도로 보여준다. 기존 모델 파일은 교체 성공 후에도 보존한다.

메모리 예상치는 참고값이다. context/KV cache와 동시 작업에 따라 달라지므로 실행 보증으로 쓰지 않는다. 서비스 cgroup 메모리를 GPU 전용 메모리로 표기하거나 UMA 사용량을 중복 합산하지 않는다.

## 8. 자동 찾기: 탐지 → 후보 → 검증 → 등록

상단 [서비스 찾기]를 눌렀을 때만 실행한다.
1. 사용자 systemd unit과 활성 상태를 일괄 조회.
2. 등록/선택한 로컬 포트에 한해 제한된 읽기 전용 API 탐지.
3. 명시된 모델 경로의 작은 메타데이터/index만 검색. 파일명·포트만으로 엔진/양자화/context를 확정하지 않는다.
4. 후보별 탐지 근거와 “제어 가능/조회만 가능/수동 설정 필요” 표시.
5. 사용자가 후보를 등록하면 초기에는 읽기 전용. 검증한 manager binding에 대해서만 제어 활성화.

중복 제거 키는 사용자+unit, 또는 로컬 endpoint+engine identity. 샤드는 디렉터리/index로 묶는다. 삭제된 파일은 “경로 없음”, 삭제된 unit은 “서비스 없음”으로 표시하고 등록 해제와 실제 파일 삭제를 분리한다. 개별 .safetensors나 config.json만으로 완성 모델이라고 선언하지 않는다.

검색 상한: roots 8, 깊이 5, 항목 10,000, 후보 128, 전체 2초. 디렉터리 순회 중에도 시간 제한을 확인한다. 기본적으로 경로 밖 symlink를 따라가지 않는다. HF 캐시 등 연결 구조는 선택한 루트 안에서 별도 지원하거나 수동 등록 안내한다. 전체 디스크/전체 포트 상시 스캔, 가중치 로딩/해시, 자동 다운로드는 초기 범위에서 제외한다.

## 9. 가벼운 조회와 제한

- 서버+트레이 480 MiB 한도, 기존 5초 호스트 수집 및 720개 이력 유지. 별도 DB/Prometheus/Grafana/상주 AI 에이전트 없음.
- 모델 화면이 보일 때 서비스 상태를 5~10초 공유 캐시로 조회. 여러 브라우저가 같은 수집을 반복하지 않게 single-flight 처리한다.
- 기존처럼 서비스마다 subprocess를 직렬 실행하는 대신 제한된 unit 묶음을 한 번에 systemctl show로 조회한다.
- 자세한 엔진 지표는 선택된 상세창/표시 중 카드에 필요한 항목만 조회한다. 종료된 서비스에는 API를 반복 호출하지 않는다. 실패는 backoff.
- 요청 없을 때 일반 상태/지표 수집 없음. 사용자가 시작한 작업의 완료 확인만 제한시간 내에서 계속한다.
- 기본 probe 응답 256 KiB, metrics 1 MiB, 동시 probe 2, timeout 1~2초. 상한 초과는 미확인이지 빈 큐가 아니다. bounded worker는 8개 HTTP worker를 잠식하지 않도록 캐시 결과/갱신 중 상태를 먼저 반환한다.
- 로그는 사용자가 펼칠 때만 최근 200줄/64 KiB. 원시 프롬프트·키·환경변수는 반환하지 않고, 축약된 작업 오류를 기본 표시한다.
- 로컬 endpoint/허용 포트만 읽는다. 리다이렉트/임의 외부 URL 접근 금지. 실제 비밀값은 로컬 private secret 참조로만 보관한다. [열기]는 별도로 등록한 실제 접근 가능 URL을 사용하며 휴대폰에 localhost 주소를 건네지 않는다.
- 구현 뒤 실제 cgroup memory/current/peak, 다중 브라우저 수집 횟수, 유휴 수집 정지를 측정한다. 현재 관측 메모리나 프레임워크 선택만으로 새 기능 부담을 보장하지 않는다.

## 10. 저장·API·마이그레이션 제안

개인 디렉터리의 services.json 한 파일에 registry_schema, revision, services, profiles, assets를 저장한다. 기존 config schema 1과 인증 파일은 유지한다. 0600, 파일 잠금, validate → 임시 파일 fsync → atomic replace → 메모리 스냅샷 교체. 로컬 LLM용 CLI와 웹 저장이 같은 검증기를 사용한다.

- GET /api/services: 캐시 관측, 기능 지원, 마지막 관측 시각.
- POST /api/services/discover: bounded 후보 검색. 파일 변경/실행 없음.
- POST /api/services/validate: 후보 또는 프로필의 검증 결과·변경 요약.
- POST /api/services/register: 검증된 후보 ID와 허용된 메타데이터만 저장.
- POST /api/services/{id}/action: action, profile_id, expected_revision, idempotency_key. shell/환경변수/endpoint 입력은 거절.
- GET /api/operations/{id}: 접수/진행/완료/실패/복구 상태.
- POST /api/services/unregister: 실행 중이면 차단. 등록만 제거, 모델·unit 파일 보존.

프로필의 실행 대상 변경은 초기에는 로컬 CLI/LLM 설치 작업에서만 허용하고 웹에는 검증된 선택지·표시 이름·기본 프로필 편집을 제공한다. 지원되지 않는 설정은 임의 입력란으로 열지 않는다.
변경 시 expected_revision으로 오래된 화면/다른 기기의 덮어쓰기를 막는다. 등록 수 32, 프로필 총 64, 자산 기록 128을 초기 상한으로 둔다.

기존 models[]는 자동 시작 없이 읽기 전용으로 변환 결과를 미리 보여준다. 기존 allow_control 의도는 기록하되 unit 소유/관리 가능 여부를 재검증한다. 활성화 전 원본을 백업한다. 새 레지스트리가 존재하면 구 설정과 이중 제어하지 않는다. 구 API는 등록된 기본 프로필로 매핑하는 호환 계층을 한 버전 유지한다. 잘못된 파일은 마지막 정상 설정을 유지하고 오류를 표시한다.

제안 모듈: service_registry.py(검증/저장), service_manager.py(상태/작업/잠금), adapters/(고정 엔진 연결), discovery.py(후보), web/service-controls.js + css(화면). 기존 호스트 측정 및 지표 상세 코드를 분리 유지한다.

## 11. 구현 순서와 완료 기준

1. 레지스트리·manager·관측 상태 및 읽기 전용 카드. 실제 세 서비스의 설치 방식/포트/버전/API를 확인하고 등록 초안을 만든다.
2. 임시 테스트 user unit으로 시작/정지/실패/시간 초과/중복 요청/재시작 복구를 검증한 후 실제 서비스 제어 연결. 테스트 목적으로 실행 중 사용자 작업을 중단하지 않는다.
3. ComfyUI 준비/큐, Qwen 실제 엔진 식별/준비, Hermes 지원 상태 신호를 차례로 연결. 모르는 데이터는 그대로 표시.
4. 후보 검색→등록 UI와 기존 설정 마이그레이션. LLM 추가 가이드/검증 CLI.
5. 프로필 교체·충돌·복구, 엔진 버전 변경 감지. vLLM/llama.cpp/LM Studio 등은 실제 설치 요청과 버전 검증 후 추가.

검증: 다른 브라우저 동시 시작/정지, unit 없음·권한 없음, engine API 미지원/401/비정상 응답/시간 초과, 큰 큐 응답, 포트 충돌, 이전 모델 복구 실패, 모델 경로 제거, 비밀값 미노출, 재부팅/업데이트 후 로그인·레지스트리 유지, 320/390px KO/EN, 무접속 수집 정지, 전체 cgroup 한도.

이번 변경은 설계 파일만 추가한다. 서비스 시작·정지·재시작, 실제 등록 파일 수정, 패키지 업데이트, GitHub 공개는 수행하지 않는다.
