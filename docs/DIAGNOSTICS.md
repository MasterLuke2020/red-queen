# Diagnostics and Health

## System Status API

Stable service: `wnhf.system_status`  
API version: `1.3`  
Health score model: `release-scope-2.1`

The status aggregates runtime state, registry state, current validation, decisions, policies, capabilities, release scope, scheduler state and the latest canonical public execution.

### Important semantics

- `healthy` means no active required failure and no in-scope warning affecting current release readiness.
- planned-domain diagnostics are classified outside current release scope and do not masquerade as RC blockers.
- no canonical execution since startup is `informational`, not a warning.
- explicit system-status calls refresh registry validation instead of relying only on an early startup snapshot.

## Execution runtime health

`wnhf.execution_runtime_health` distinguishes:

- `declared_actions` — action exists in the semantic capability registry;
- `semantically_ready` — action resolves to available, healthy providers;
- `real_execution_enabled` — canonical real-execution request contract exists;
- `executable_now` — semantic readiness plus real-execution enablement.

At RC1 the verified expected counts are 5 declared, 5 semantically ready, 1 real-execution enabled and 1 executable now.

## Provider diagnostics

Provider diagnostics expose contract validity, discovery, availability, health, qualification and capability binding. Provider qualification is derived from canonical execution evidence rather than a parallel installation-specific hard-coded evidence model.

## Validation quality

The live RC1 reference installation passed registry validation with quality score `100`, zero errors and zero warnings. Intentionally disabled objects may appear as informational items rather than health warnings.

## Recovery mode

If required registry loading fails at startup, Red Queen can create a recovery house model and expose recovery diagnostics instead of proceeding as though the registry were healthy.
