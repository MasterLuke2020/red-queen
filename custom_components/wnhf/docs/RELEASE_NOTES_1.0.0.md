# Red Queen 1.0.0 — Stable Release Notes

Red Queen 1.0.0 is the first stable release of the semantic home framework for Home
Assistant. It promotes the fully qualified RC14 feature set without adding a new
feature domain or changing the canonical physical execution contract.

## Stable identity

- Red Queen `1.0.0`
- Home Assistant domain `wnhf`
- WNHF baseline `1.40.0`
- `WP-4.7.20.0`
- Canonical execution API `1.0`
- Canonical real-execution contract `2.3-rc11`
- 8 capabilities
- 23 semantic actions
- 16 canonical real-execution contracts
- 68 Home Assistant services

## Included stable surface

- Managed commissioning and transaction-safe configuration.
- Stable semantic IDs and explicit manual/managed ownership modes.
- Native Home Assistant entities for supported Red Queen objects.
- Generated `/red-queen` dashboard.
- Entity/Provider diagnostics and dashboard source freshness.
- Read-only Migration & Repair preview.
- Explicit source-SHA guarded manual → managed adoption with mandatory backup.
- Guided managed repair for supported entity and HA area/floor references.
- Guarded canonical execution including `garage.stop`.
- HACS repository metadata and Red Queen brand assets.

## Qualification

Functional and HACS qualification are LIVE VERIFIED, including clean install, RC14
upgrade, restart persistence, recovery/fail-closed behavior, config-entry
remove/re-add, HACS clean installation and HACS redownload while preserving
`/config/wnhf` byte-identically.

The final release archive is built from the stable source freeze and qualified exactly
before publication.

Climate, media and larger Plant Care remain deferred beyond 1.0.
