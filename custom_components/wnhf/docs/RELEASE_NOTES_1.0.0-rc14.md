# Red Queen 1.0.0-rc14 — Development Notes

RC14 is the controlled migration and repair hardening release on the path to stable
Red Queen 1.0.0.

Development identity:

- Red Queen `1.0.0-rc14`
- WNHF `1.40.0`
- `WP-4.7.20.0`
- Canonical execution API `1.0`
- Canonical real-execution contract `2.3-rc11`

## WP14.1 — Migration & Repair Preview Foundation

- Adds a strictly read-only migration/repair analyzer.
- Exposes Migration & Repair for manual and managed registries.
- Detects duplicate semantic IDs and orphaned room references.
- Detects malformed/incomplete managed-maintenance object shapes.
- Reuses production entity diagnostics for explicit HA references.
- Checks stored HA area/floor links when present.
- Computes deterministic source bundle SHA-256 and proposed managed file ownership.
- Reports migration eligibility only for a valid manual source with zero blockers.
- Treats missing/disabled configured entities as blockers and runtime-transient states
  as warnings.
- Never creates an ownership marker or writes registry data in WP14.1.

## Compatibility and safety

- Manual registries remain read-only.
- Managed mutation behavior from RC13 is unchanged.
- Canonical execution API remains `1.0`.
- Canonical real-execution contract remains `2.3-rc11`.
- No physical action, service, capability or provider contract is added.
- Climate/media/large Plant Care expansion remains deferred.

Live qualification, accepted migration transactions and publication remain future
RC14 gates.
