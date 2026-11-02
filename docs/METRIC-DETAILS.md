# Metric detail dialogs / 지표 상세창

Status: included in 0.3.0. Earlier private-build evidence remains in [the live deployment record](development/METRIC-DETAILS-LOCAL-VALIDATION.md); current release validation is in [0.3.0](releases/0.3.0.md).

## Information architecture

Every overview card opens an independent dialog. No resource sidebar or combined performance screen. Retain the existing square geometry, dark surfaces, lime accent, Chakra Petch / Rajdhani / SUIT typography and 300ms entry / 200ms exit, with reduced-motion support.

| Card / 카드 | Headline readings / 핵심값 | Breakdown / 세부 정보 |
| --- | --- | --- |
| GPU | Utilization, SM clock, GPU temperature, GPU power | GPU identity, memory clock when exposed, clock event causes |
| CPU | Total utilization, min/max exposed core clock, detected logical CPUs | Dynamic per-core utilization, architecture |
| Memory / 메모리 | Used, available, used/OS total %, swap used | Composition; firmware-installed vs OS usable capacity; clock capability |
| SSD | Used, available, used/total %, filesystem capacity | Composition bar and root mount; reserved space, precise capacity and df accounting in a collapsed disclosure; no history/range statistics |
| Temperature / 온도 | GPU current, selected-range average/peak, thermal event status | NVML GPU plus hwmon sensor list with source identity; no inferred CPU/SoC labels |
| GPU power / 전력 | Current, selected-range average/peak, power-limit events | GPU scope, related load/temperature, decoded events; no wall-power estimate |
| Network / 네트워크 | Receive/send, range peaks | Shared-scale two-line history, included physical interfaces, decimal rate units |
| Disk I/O | Read/write, range peaks | Shared-scale two-line history, included whole block devices; no invented IOPS/latency |

### Progressive disclosure

Keep operational values visible: per-core load, installed versus OS-usable capacity, sensor temperatures with their source family, and current clock-limiting events. Move included network interfaces/block devices, sensor raw identifiers, memory-clock availability, units and calculation explanations into the existing collapsed notes. CPU architecture and core-clock range are already in the heading/headline, so do not repeat them below the graph. Power context explicitly says GPU only. Temperature/power average and peak appear once in the headline; network/I/O retain only average below the graph because peaks are already above it. Dynamic diagnostic values refresh inside the mounted disclosure, preserving its open state, focus and scroll position. SSD retains its existing capacity-only layout.

## Data contract and behavior

- Reuse `liveNode.sample`, `history` and `hardware`. No extra endpoint calls, polling, GPU contexts, agents or server dependencies. The original design prototype remains independent.
- `web/telemetry-detail-data.js` contains pure calculations. `web/live-metric-details.js` overrides the installed detail entry/render functions after `runtime.js`; its stylesheet is scoped to `.telemetry-detail` and `td-*` classes.
- If a detail asset fails to load, the installed runtime shows a reload instruction; it never falls back to the prototype's generated details. Overview mini-charts retain an independent five-minute window.
- API fields and units remain unchanged. GiB/TiB use powers of two; MB/s uses 1,000,000 bytes/s. Headline rates switch to decimal GB/s above 1,000 MB/s. Graphs retain MB/s for consistent range comparison.
- SSD capacity is a current-state view: no chart, range buttons or average/peak section. Its headline readings, composition bar and expanded capacity rows still refresh from the shared five-second sample; the disclosure stays mounted during updates.
- CPU/GPU charts use 0–100%. Memory uses `memory_total_gib`. I/O uses a shared tiered axis; temperature and power have presentation floors, not inferred hardware limits. The axis cannot shrink until the dialog is reopened; each selected range has independent scale state.
- Graphs cover wall-clock time, not equally spaced sample indexes. Null values and gaps longer than 15 seconds break traces. Single valid points remain visible. Zero is a real reading. Statistics count only valid samples and include zero, without filling collection gaps.
- Server history is shared, in-memory and bounded at 720 samples. One-hour selection does not imply a complete hour exists. Actual sample count and missing gaps are visible.
- A disconnected or older-than-15-second sample is marked as retained, with its original timestamp. Current readings stay visible to aid diagnosis. Sensor absence is not reported as zero or normal health.
- Controls and the notes disclosure remain mounted during updates; only data regions are patched. Keep scroll and focus. Add native `summary` elements to the existing focus trap and exclude hidden elements. Restore focus to the originating card on close.
- NVML clock event bits follow the [official NVIDIA reference](https://docs.nvidia.com/deploy/nvml-api/latest/api/group__nvmlClocksEventReasons.html). Thermal events are bits 32/64; software power cap and external power brake are 4/128. Idle and clock policies are not thermal events. Generic hardware slowdown does not identify its cause. Preserve unknown bits; unsafe integer masks remain unknown.
- Sensor labels are driver labels; generic ACPI readings are numbered without guessing physical location. Reported sensors may overlap physically. Only GPU temperature is charted.

## Validation

Run `node --test tests/telemetry-detail-data.test.cjs` and syntax-check all `web/*.js`. The tests cover zero/null distinction, time windows, gaps and isolated points, 64 GiB capacity, scale stability, reserved space and clock event decoding. Backend regressions use `python3 -m unittest discover -s tests -v` on Linux.

Browser QA covers all eight dialogs on desktop and 390/320px widths, Korean/English, stale/missing/zero/large readings, range selection, disclosure persistence and keyboard dismissal. See [design QA](../design-qa.md) for executed checks and remaining platform gaps. Test fixtures and screenshots live outside the distributable repository; fixtures never ship in the installed runtime.
