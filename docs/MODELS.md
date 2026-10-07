# 모델 추가·교체 / Model integration

0.1은 **이미 설치된 모델의 사용자 systemd 서비스**를 등록한다. 자동 다운로드·삭제·프로세스 탐색 기반 등록은 하지 않는다. 다른 LLM에게 이 문서와 AGENTS.md를 먼저 읽게 한다.

`~/.local/share/dgx-spark-control/config.json` 예시:

```json
{
  "schema_version": 1,
  "spark_name": "DGX_SPARK",
  "model_roots": ["/your/configured/models"],
  "models": [
    {"id": "my-llm", "name": "My LLM", "engine": "llama.cpp", "service": "my-llm.service", "allow_control": true}
  ]
}
```

기존 토큰 파일과 설정 필드를 보존하고 필요한 항목만 병합한다. 서버는 현재 config를 시작 시 읽으므로 파일을 수동 변경한 뒤 `systemctl --user restart dgx-spark-control`로 적용한다. 화면의 Spark 이름 저장은 재시작 없이 적용된다.

1. 사용자에게 설치·교체 요청의 범위를 확인한다. 실행 중인 모델과 다른 사용자의 작업을 조사한다.
2. 모델 경로·리비전·샤드·아키텍처·런타임 호환성을 검증한다. 파일명만 보고 컨텍스트·양자화·성능을 확정하지 않는다.
3. 기존 서비스가 없으면 사용자가 승인한 실행 명령으로 별도 user systemd unit을 만든다. 모델은 대시보드 서비스의 자식으로 실행하지 않는다.
4. `systemctl --user status my-llm.service`와 엔진 health/실제 추론을 별도로 확인한다.
5. registry에 항목을 추가한다. `allow_control:false`로 상태만 먼저 볼 수 있다.
6. 기존 작업에 영향을 주지 않는 조건에서 시작·중지·실패 처리를 검증한다. 모델 파일은 이 대시보드가 삭제하지 않는다.
7. 문서·버전 변경 기록에 지원 엔진/검증 결과/남은 한계를 갱신한다. 실제 개인 경로는 공개 문서에 넣지 않는다.

후속 엔진 어댑터 계약: `status`, `ready`, `model_identity`, `capabilities`, `metrics`, `start`, `stop`. Prometheus exporter 전체 스택 없이 엔진 `/metrics`를 직접 읽을 수 있으나 원본 response 크기·timeout·캐시 상한을 둔다. 서비스 active와 추론 ready를 분리한다.

후속 개발 대상: vLLM/llama.cpp/커스텀 TensorFold의 tok/s, 컨텍스트, KV cache, 대기 요청. 지원하지 않는 엔진에 다른 엔진의 지표 이름을 적용하지 않는다. ComfyUI 작업 큐는 별도 어댑터가 필요하다.
