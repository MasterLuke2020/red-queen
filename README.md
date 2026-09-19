# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house as
semantic objects and state, resolves native/canonical controls, and exposes a stable
Home Assistant surface for commissioning, operation and diagnostics.

> **Current candidate:** `1.0.0-rc14` — FINAL EXACT PACKAGE LIVE VERIFIED
> **Technical Home Assistant domain:** `wnhf`
> **Development lineage:** WNHF `1.40.0` / `WP-4.7.20.0`

## RC14 candidate changes

RC14 completes the controlled migration and repair hardening planned before stable 1.0.

- Adds read-only Migration & Repair preview for manual and managed registries.
- Detects structural blockers, duplicate IDs, orphan-room references and configured
  entity health problems.
- Adds deterministic source bundle SHA-256 protection.
- Adds explicit, confirmed manual → managed adoption with mandatory source backup.
- Adds guided managed repair for missing/disabled configured entity references.
- Adds guided repair of invalid stored HA area/floor source links.
- Preserves semantic object IDs through repair.
- Reuses complete candidate validation and transaction backup/rollback.
- Refuses stale migration/repair writes when the source changed after preview.
- Never silently adopts manual configuration.
- Does not change the canonical physical execution contract.

## Current canonical real-execution surface

```text
lighting.turn_on
lighting.turn_off
covers.open
covers.close
covers.blades_open
covers.blades_close
garage.open
garage.close
garage.stop
openings.lock
openings.unlock
openings.release
notifications.send
notifications.announce
notifications.route
plants.record_watering
```

Canonical execution entry point: `wnhf.execution_execute`
Canonical execution API: `1.0`
Canonical real-execution contract: `2.3-rc11`

## Qualification status

RC14 WP14.1, WP14.2 and WP14.3 are functionally live-qualified. The immutable package
built from freeze commit `5ec86514f96f88104a3531f669ca3d58b49910cb` was then
clean-installed and requalified on the isolated Home Assistant test instance.

Final qualified package:

- Integration files: `180`
- Archive: `red_queen_1.0.0-rc14_final_candidate.zip`
- SHA-256: `a30b91ae143dfb089795d623b45fd26483f9dc6bad0852374b6d0f8f1bc1ad98`

The exact package passed startup, managed-registry loading, clean diagnostics,
Migration & Repair, generated dashboard operation and restart persistence. The frozen
integration source was not changed after packaging.

See `docs/RC14_CANDIDATE_VALIDATION.md` and
`custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc14.md`.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home
Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Installation-owned semantic data remains below `/config/wnhf`. Existing manual
registries are not silently adopted or rewritten.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
