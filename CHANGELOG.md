# Changelog

## 0.1.0 — 2026-10-08

- First installable Spark-hosted runtime: one Python process, no external Python dependencies.
- Cached on-demand NVML/Linux telemetry, eight live cards and real sample history.
- Fresh-install name `DGX_SPARK`; Settings persists the shared name on the Spark.
- Token-protected API, explicit user-service start/stop, bounded model candidate discovery.
- Versioned installer, checksum-verified update path, previous-code rollback and config backups.
- Whole dashboard service limit 480 MiB (<512 MB), no swap, bounded workers/history.
- Korean/English runtime, existing responsive visual language and modal transitions preserved.
- LLM handoff, architecture, model integration, installation and release documentation.

Limits: request queue, inference throughput and engine readiness adapters are future work; long-term persistent telemetry is disabled. Consult docs/releases/0.1.0.md for validation status.
