# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house
as semantic objects and state, resolves native/canonical controls, and exposes a
stable Home Assistant surface for commissioning, operation and diagnostics.

> **Current candidate:** `1.0.0-rc13` — FEATURE LIVE VERIFIED / RELEASE FREEZE
> **Technical Home Assistant domain:** `wnhf`
> **Development lineage:** WNHF `1.39.0` / `WP-4.7.19.0`

## RC13 candidate changes

RC13 hardens commissioning and day-two maintenance on top of the RC12 generated
dashboard foundation.

- Adds transaction-safe managed editing for rooms, lights, covers, openings and plants.
- Keeps semantic object IDs stable during maintenance.
- Adds enable/disable and guarded deletion with explicit second confirmation.
- Prevents deletion of referenced rooms and the last managed room.
- Adds Entity/Provider diagnostics for configured references only.
- Classifies missing, HA-disabled, unavailable, unknown and state-missing references.
- Marks the generated dashboard outdated when the semantic registry source changes.
- Keeps dashboard create/update explicit and restart persistence non-destructive.
- Fixes the `Invalid flow specified` dashboard Options Flow completion regression.
- Keeps manual registries read-only and never silently adopts them.
- Keeps the canonical physical execution contract unchanged.

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

The RC13 feature set was live-qualified on a dedicated Home Assistant test instance
on 2026-09-17 using the exact post-fix candidate at commit
`4f35dd96ed9254ca49cc86f0d27d5ead025c24d9`.

Qualification covered fresh managed commissioning, managed object creation and
maintenance, enable/disable, guarded deletion, diagnostics, dashboard
create/update/freshness, restart persistence and the dashboard Options Flow regression
fix. The diagnostic checkpoint reported 21 configured references, 21 ready and
0 findings.

This release-freeze commit changes release metadata/documentation only. A final
immutable RC13 package is built from the frozen integration source and receives a
short exact-package startup/dashboard/diagnostics/restart requalification before tag
and prerelease publication.

See `docs/RC13_CANDIDATE_VALIDATION.md` and
`custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc13.md`.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home
Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Installation-owned semantic data remains below `/config/wnhf`. Existing manual
registries are not silently adopted or rewritten by the managed configurator.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
