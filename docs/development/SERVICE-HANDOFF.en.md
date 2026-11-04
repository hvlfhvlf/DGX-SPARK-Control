# LLM service/model handoff — 0.3.2

Start with the [agent playbook](../LLM-GUIDE.en.md) for copyable installation, registration, display-edit and model-switch prompts. Web registration supports connection review and optional control of existing user services; advanced local registry changes follow the steps below.

Read AGENTS.md and ../MODELS.md first. The design research includes future scope; do not assume all proposed features exist.

1. Inspect current services and workloads without printing raw credentials, environment, full commands or model paths to public output.
2. Separate installation from registration. Preserve installed engines, weights, drivers and working units. Install a new engine only within the user's requested scope.
3. Choose process/hermes/comfyui/openai-compatible based on verified endpoint behavior. Process state is not inference readiness. Engine-auth secret references and load/unload APIs are not implemented.
4. Keep launch commands and environment files in existing local user systemd units. Models must not run inside the dashboard cgroup.
5. Export the private registry to a private local file with umask 077. Merge stable service/profile/asset IDs, known dependency and exclusive groups; never commit this file.
6. Run `dgx-spark-control services check --file FILE`. Inspect missing_units. Back up the current revision, then apply with `dgx-spark-control services apply --file FILE --expected-revision N`. No automatic start occurs. Concurrent operations/edits are rejected.
7. Stop a service before selecting/rebinding its profile. Start only the requested service. Do not interrupt other workloads to benchmark. Test disposable units for lifecycle behavior.
8. Observe process status and API readiness separately from actual inference. A failed or timed-out start can leave a running process. Inspect local status before retrying. Recovery is stop → previous profile → start; automatic switch rollback is not implemented.
9. Record engine version, tested behavior and limitations privately. Keep published examples generic. Do not publish to GitHub without the user's explicit instruction.

ComfyUI checkpoint additions normally reuse its service. Hermes provider changes are separate from gateway control; verify actual dependencies rather than assuming a specific local model.
