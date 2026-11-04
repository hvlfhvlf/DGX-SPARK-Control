# 서비스·모델 연결 / Services and models

0.3.2: **설치된 사용자 systemd 서비스**를 등록합니다. Dashboard runs no inference engine itself. Engine/weight installation and deletion remain separate tasks.

## Structure / 구조

- **Service**: stable card (application, inference server or gateway), with an adapter and selected default profile.
- **Profile**: existing `systemd-user` unit, local API probe, timeout, optional resource/port conflict groups and known dependencies.
- **Asset**: optional operator-supplied model name/ID metadata; not a runnable command or a guessed context/quantization value.
- Private file: `~/.local/share/dgx-spark-control/services.json`, registry_schema 1. Separate from config schema 1, password, sessions and maintenance token.

기존 `config.json.models`는 첫 실행에 한 번 옮깁니다. 기존 파일은 보존하며 서비스를 자동 시작하지 않습니다. 이후 새 레지스트리만 제어 기준입니다. Legacy `/api/models` endpoints map to this registry; do not maintain two independent allowlists.

## Add / 추가

1. Install and validate the engine separately. Keep its existing user unit; do not replace working drivers, weights or launch scripts.
2. **Models → Add service** lists existing user services. Select one, enter its local API port, explicitly enable control if needed, then check and save. Earlier releases used read-only Find services plus local CLI registration. No whole-disk/port scan or automatic control authorization is performed.
3. For advanced settings, alternatively export the private registry to a private working file **on Spark**; never paste this output into public chat or commit it:

```bash
umask 077
dgx-spark-control services export > ~/.local/share/dgx-spark-control/services-edit.json
# Edit this private file locally; retain existing services and profiles.
dgx-spark-control services check --file ~/.local/share/dgx-spark-control/services-edit.json
dgx-spark-control services apply --file ~/.local/share/dgx-spark-control/services-edit.json --expected-revision N
```

`N` is the revision in the exported file. Apply checks schema, existing units and revision, then writes atomically; it never starts services. Conflicting edits or operations are rejected. The running server detects changes without a restart. Run as the normal Spark user, without sudo.

`check` reports `missing_units`; valid JSON alone does not prove engine health. `export` initializes an empty registry if absent; it is not a pure pre-install check.

The web Connection editor can bind a discovered existing user unit and configure a local API port, adapter, control permission and app URL after review. Advanced timeouts/dependencies remain local registry settings. Web requests accept IDs/actions, never commands or arbitrary probe URLs. Use [the generic example](development/SERVICE-REGISTRY.example.json), not someone else's personal registry.

## Replace / 교체

Add a verified profile under the same service ID. Stop the service, select the new profile in Details, then Start. Selection does not delete weights or start the model. A running selected profile cannot be rebound by CLI. 기존 모델은 보존하며 다시 정지 → 이전 프로필 선택 → 시작으로 복구할 수 있습니다.

Automatic stop/switch/start rollback is intentionally not shipped in 0.3.1. If startup times out, the process may still be running: inspect the current state and local systemd journal before retrying. A completed operation is a point-in-time observation, not a guarantee of future health.

ComfyUI checkpoint additions normally do not require another service. ComfyUI updates should preserve its unit and recheck API contracts. Hermes provider configuration is distinct from its gateway service; do not assume it uses a particular local model.

## Adapters / 지원 범위

| Adapter | What is measured | Limits |
| --- | --- | --- |
| process | systemd process state | No inference readiness or job count |
| hermes | Gateway process state | Provider connectivity and active conversations unknown |
| comfyui | `/system_stats`, running/pending queue counts | Never returns workflow/prompt bodies; no cancel/interrupt/load action |
| openai-compatible | `/v1/models` response and count | Readiness probe; separate inference adapters read supported metrics without running a benchmark |

Probe origin must be `http://127.0.0.1:PORT` (1024–65535). No credentials, remote hosts, redirects or proxy environment. Authentication-required engine endpoints currently use process-only status; secret_ref support is not shipped. Model IDs/paths in raw API responses are not forwarded. `open_url` is separately configured for a browser-reachable application, not guessed from localhost.

LM Studio, vLLM, llama.cpp and other engines may use existing user units for lifecycle control after local verification. Engine-specific model load/unload, sleep/wake and Docker/native-process management remain future adapters. Supported inference metrics are described below.

## Runtime / 운영

One in-flight control operation globally, finite worker/timeouts, at most 200 persisted operation summaries. A server restart marks unfinished operations interrupted and never replays them. Process states are batched and cached 5 seconds across clients. At most two HTTP adapter probes are selected per refresh; each response is capped at 256 KiB with socket/deadline limits. Service polling is demand-driven by visible dashboard views, except completion monitoring for an accepted operation.

Registered exclusive groups and known dependency relationships block unsafe overlap. They cannot infer unregistered workloads, all resource needs or Hermes provider settings. Start refuses an occupied configured probe port when the selected service is stopped. Stop/restart require an explicit UI confirmation and may interrupt work.

Logs, execution commands, private model paths and secrets remain local. A raw-log viewer is deliberately omitted. Model-root discovery in Settings is separate and does not establish engine compatibility.

Start with the copyable [한국어 agent playbook](LLM-GUIDE.ko.md) or [English agent playbook](LLM-GUIDE.en.md).

Read [한국어 LLM 가이드](development/SERVICE-HANDOFF.ko.md), [English handoff](development/SERVICE-HANDOFF.en.md), and [design research / future scope](development/MODEL-SERVICES-PLAN.md).


## App links and display metadata / 앱 바로가기·모델 표시

Optional profile fields `model_name`, `quantization`, `inference_engine`, `serving_engine` contain verified display names (max 120 characters), not command lines, keys or absolute model paths. Set them when adding/replacing a profile; they are operator metadata and do not assert that a stopped model is loaded. `open_url` is the existing browser-reachable application address. It appears on the card and in Details; it is separate from the loopback probe. Credentials, URL query tokens and fragments are rejected. The button opens the existing app; its own login remains in effect. Do not change networking or expose a service just to populate the link.

모델 풀네임을 카드 제목으로, 그 아래에 양자화를 표시하고 추론·서빙 엔진은 작은 보조 정보로 표시합니다. 모델 교체 시 함께 갱신하며 양자화는 설치된 설정에서 확인하고 추측하지 않습니다. 미확인 값은 null로 남깁니다. ComfyUI/Hermes 주소는 각 Spark의 개인 설정에만 저장합니다. 공개 예제에는 실제 접속 주소를 넣지 않습니다.

The card title uses the full model name, followed by quantization and smaller inference/serving metadata. Confirm quantization from installed configuration; use null when unverified.

## Display editing and order / 표시 편집·순서

Models → pencil edits `name` (service, required, max 80) and the selected profile's `model_name`, `quantization`, `inference_engine`, `serving_engine` (optional, max 120 each; blank clears). Order saves an exact permutation of all service IDs. Both require authentication, same-origin requests and the current registry revision. Conflicting edits/operations are rejected. Saving does not start, stop or reconfigure any engine. The same registry is shared across devices and survives dashboard restart. Display edits do not change launches or permissions. The adjacent Connection section edits reviewed API/app/control settings; executable commands remain local.

모델 탭의 연필 버튼은 표시 정보와 연결 설정을 별도 탭으로 편집합니다. 순서 변경은 전체 서비스 ID의 순서만 저장합니다. 활성 프로필이 바뀌거나 다른 기기가 먼저 저장하면 창을 다시 열어 최신 정보를 확인합니다. 엔진/모델 설치·실행 설정 변경은 기존 로컬 CLI 절차를 사용합니다.

App access is configured separately from dashboard access. A Tailscale connection does not override an engine app’s device allowlist, bind address, authentication or network policy. No personal ComfyUI gateway or Tailscale policy is bundled with this package.

대시보드 접속과 앱 접속은 별도입니다. Tailscale 연결만으로 앱 자체의 기기 허용 목록·바인딩 주소·인증·접근 정책이 해제되지 않습니다. 이 패키지는 개인 ComfyUI 게이트웨이나 Tailscale 정책을 배포하지 않습니다.


### Startup observer
Optional profile field `startup_observer: "tensorfold"` reads bounded journal records scoped to the current systemd InvocationID. Layer count measures weight loading, not total startup time. The serving marker is distinct from an API probe. Unknown engines omit percentages. Failed Start clears the unit start-limit only when MainPID is zero; it does not kill other processes or change memory configuration.


## Inference and web registration
Overview shows aggregate output/input token throughput on the left and the selected LLM service on the right. TensorFold, vLLM and Strata adapters expose only available metrics. Input is token-counter delta per elapsed second, not prefill compute speed. Output uses an engine window or counter delta; inspect Measurement notes for its source. Completed-request counters may be bursty. No prompts or completions are collected.

History is collected on demand every 5 seconds while Overview is open, with 5m/30m/1h views. Up to four streams of 720 samples are held in memory and cleared on restart. Missing samples remain gaps. Zero is valid for an idle engine.

Models → Add service → select an existing user systemd service → choose adapter, local API port and optional app URL → enable control if desired → Check connection → Save. Saving does not start it. Stopped services can be registered with unverified API readiness, then started. The API is local to this Spark: if loopback refuses the connection, only an OS-verified local IPv4 listener may be used. No arbitrary shell commands or remote probe URLs are accepted. Connection settings edit observation and control settings; they do not change the engine command.

An additional existing service can be added as a profile to an existing card. Stop before selecting a different profile, then start. Model files lets you save scan roots, discover candidates and register filenames/display names in a private inventory. Inventory registration does not create launch commands. Engine/weight download or deletion, direct Docker/system-service control and generating engine launch templates from files remain outside this release.

### Editor navigation
Existing connection settings now live under the card pencil → Connection, alongside Display. Section drafts survive switching; each section saves separately with its existing revision checks. Cards no longer have a separate CONNECTION button. Registration, API security and lifecycle behavior are unchanged.
