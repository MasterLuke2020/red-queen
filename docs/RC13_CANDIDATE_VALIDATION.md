# RC13 Candidate Validation

## Current state

**DEVELOPMENT — NOT YET A RELEASE CANDIDATE**

- Red Queen: `1.0.0-rc13`
- WNHF: `1.39.0`
- Work-package baseline: `WP-4.7.19.0`
- Theme: **Managed Maintenance Foundation**
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11` (unchanged)

## WP13.1 scope

RC13 begins the final product-hardening path toward Red Queen 1.0 by adding safe
maintenance of configurator-owned semantic registry objects.

The first work package adds:

- read/select support for managed rooms, lights, covers, openings and plants;
- transactional update/replace while stable semantic IDs remain immutable;
- enable/disable maintenance;
- guarded deletion with full-bundle validation;
- room-deletion protection while dependent semantic objects still reference it;
- explicit second confirmation before deletion;
- Home Assistant Options Flow maintenance screens;
- German and English maintenance translations;
- repository verifier coverage for maintenance invariants.

Every mutation continues to use the existing managed ownership marker, pre-write
candidate validation, backup creation, atomic replacement and rollback behavior.

## Qualification status

No exact RC13 candidate package exists yet. Live candidate qualification, final
source checksum freeze, hassfest and publication checks remain future release gates.

## WP13.2 — Production Diagnostics & Dashboard Freshness

WP13.2 adds read-only commissioning diagnostics for configured provider/entity
references and hardens dashboard freshness tracking.

- Missing, disabled, unavailable, unknown and state-missing entities are classified.
- Home Assistant integration/platform information is shown where available.
- Disabled Red Queen objects/modules are skipped intentionally.
- Diagnostics are available for managed and manual registries; manual remains read-only.
- Registry changes set a Configurator reminder to check the generated dashboard.
- Dashboard freshness now compares both Lovelace render SHA and registry source SHA.
- Existing RC12 dashboard manifests remain compatible.
- Canonical physical execution semantics remain unchanged (`2.3-rc11`).
