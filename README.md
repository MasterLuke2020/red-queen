# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house as
semantic objects and state, resolves native/canonical controls, and exposes a stable
Home Assistant surface for commissioning, operation and diagnostics.

> **Stable release:** `1.0.0`
> **Technical Home Assistant domain:** `wnhf`
> **Development lineage:** WNHF `1.40.0` / `WP-4.7.20.0`

## Stable 1.0 scope

Red Queen 1.0 promotes the fully qualified RC14 feature set to the first stable line.

- Managed commissioning and transaction-safe configuration.
- Stable semantic IDs and explicit ownership modes.
- Native Home Assistant lights, covers, openings, locks, garage and Plant Care.
- Native generated `/red-queen` dashboard.
- Entity/Provider diagnostics and dashboard freshness tracking.
- Read-only Migration & Repair preview.
- Explicit, source-SHA guarded manual → managed adoption with mandatory backup.
- Guided managed repair for supported entity and Home Assistant area/floor references.
- Guarded canonical physical execution, including `garage.stop`.
- HACS installation metadata and Red Queen brand assets.

No new climate, media or larger Plant Care domain is added in 1.0.

## Canonical real-execution surface

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

Stable functional and HACS qualification is **LIVE VERIFIED**.

Verified coverage includes clean fresh installation, managed commissioning, RC14 →
1.0.0 upgrade, restart persistence, fail-closed registry recovery, config-entry
remove/re-add, clean runtime operation, real HACS clean install, HACS redownload and
byte-identical preservation of `/config/wnhf`.

The final immutable `red_queen_1.0.0.zip` is built only after the stable source freeze
and is qualified byte-for-byte before the `v1.0.0` release is published.

See `docs/STABLE_1_0_VALIDATION.md` and
`custom_components/wnhf/docs/RELEASE_NOTES_1.0.0.md`.

## Installation

Preferred installation is through HACS using the Red Queen repository. Manual
installation remains supported by copying `custom_components/wnhf` to
`/config/custom_components/wnhf` and restarting Home Assistant.

Installation-owned semantic data remains below `/config/wnhf`. Existing manual
registries are not silently adopted or rewritten.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
