# Red Queen 1.0.0-rc14

Red Queen is a semantic home framework for Home Assistant. The public product name is
**Red Queen**; the technical Home Assistant domain remains **`wnhf`** for compatibility.

## Release identity

- Product: Red Queen
- Version: `1.0.0-rc14`
- Channel: `release_candidate`
- Candidate: `rc14`
- Development baseline: WNHF `1.40.0` / `WP-4.7.20.0`
- Canonical execution entry: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11`

## Managed configurator

The managed configurator supports transaction-safe commissioning and maintenance for
rooms, impulse lights, venetian blinds, windows, sliding doors, doors, garage doors and
Plant Care. Stable semantic object IDs are preserved during maintenance.

Manual registries remain read-only until an explicit RC14 migration is accepted.

## RC14 migration and repair

RC14 adds a read-only Migration & Repair preview, explicit source-SHA guarded
manual → managed adoption, and deterministic guided repair for managed registries.

Guided repair can replace a missing/HA-disabled configured entity reference with a
user-selected same-domain entity and can repair invalid stored HA area/floor source
metadata from a selected Home Assistant area.

Accepted migration/repair writes use complete candidate validation and the existing
managed backup/replace/rollback transaction. Stale source changes fail closed.

Red Queen does not auto-repair ambiguous structural findings or transient runtime
states, does not mutate Home Assistant registries during repair, and does not bypass
canonical physical execution guards.

## Diagnostics and dashboard

Entity/Provider diagnostics inspect only explicitly configured references. The managed
`/red-queen` dashboard uses native Red Queen entities through stable unique-ID binding
and tracks freshness against semantic registry changes.

`garage.stop` and all other physical controls continue through canonical guarded
execution.

## Qualification status

RC14 WP14.1, WP14.2 and WP14.3 are functionally live-qualified on isolated Home
Assistant test instances. RC14 is in release freeze for immutable exact-package
requalification.

See `docs/FEATURE_MATRIX.md`, `docs/RC14_CANDIDATE_VALIDATION.md`, and
`docs/RELEASE_NOTES_1.0.0-rc14.md`.
