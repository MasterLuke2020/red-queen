# Red Queen 1.0.0-rc1

## First public release candidate

This release introduces **Red Queen** as the public product name. `WNHF` remains the
historical development name and the technical Home Assistant domain `wnhf` remains
unchanged for compatibility.

The release candidate is cut from the live-verified WNHF 1.27.0 / WP-4.7.9.1 baseline.
The RC packaging changes product identity, release metadata, visible names and release
documentation only; the verified execution/provider/feedback/qualification machinery
is not redesigned for this release.

### Canonical execution

- Stable entry point: `wnhf.execution_execute`
- Dry-run/preflight: `wnhf.execution_dry_run`
- Canonical execution API: `1.0`
- Execution contract: `1.2-stage4.7.4`
- Canonical real action at RC1: `lighting.turn_off` (single semantic object)
- Feedback guard and idempotency protection remain mandatory where defined by provider

### Compatibility

- Integration domain remains `wnhf`
- Service IDs remain `wnhf.*`
- `/config/wnhf` remains the configuration/persistence root
- Existing entity unique IDs are retained
- Existing qualification evidence is retained
- `wnhf.execute` remains available as a legacy Decision-ID path

### Planned after the 1.0 line

Temperature/climate semantics, canonical mutating cover actions, active garage/gate
execution, media control and notifications are intentionally outside the RC1 feature
scope.
