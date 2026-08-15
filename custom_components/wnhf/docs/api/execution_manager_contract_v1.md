# WNHF Canonical Execution Manager API v1.1

The Execution Manager separates four concepts that must not be conflated:

1. **declared** — the semantic action exists in the Capability Registry;
2. **semantically ready** — its capability resolves to available, healthy providers;
3. **real execution enabled** — the action has a canonical real-execution contract;
4. **executable now** — both semantic readiness and real-execution enablement are true.

Current RC2 baseline: six actions are declared. All may be semantically ready, while
`lighting.turn_on` and `lighting.turn_off` are enabled through `wnhf.execution_execute`.

`wnhf.execution_manager` and `wnhf.execution_action` are diagnostic services.
The manager is not read-only as a product architecture: canonical execution is
active, while these two diagnostic services themselves do not dispatch hardware.
