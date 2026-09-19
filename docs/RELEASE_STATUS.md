# Release Status

## Current candidate

**Red Queen 1.0.0-rc14 — FUNCTIONAL LIVE VERIFIED / RELEASE FREEZE**

RC14 advances the lineage to WNHF `1.40.0` / `WP-4.7.20.0` and completes the
controlled migration and guided repair hardening planned before stable 1.0.

## RC14 live qualification

WP14.1, WP14.2 and WP14.3 were LIVE VERIFIED on isolated Home Assistant test instances.

PASS coverage includes read-only migration/repair preview, manual registry blocker
handling, source-SHA fail-closed refusal, explicit manual → managed adoption, mandatory
byte-faithful source backup, restart ownership persistence, guided missing-entity
reference repair, repair stale-source refusal and guided HA area/floor-link repair.

## Compatibility and safety

- Home Assistant integration domain remains `wnhf`.
- Canonical execution entry remains `wnhf.execution_execute`.
- Canonical execution API remains `1.0`.
- Canonical real-execution contract remains `2.3-rc11`.
- 8 capabilities, 23 semantic actions, 16 canonical real contracts and 68 services.
- Manual registries are never silently adopted.
- Guided repair is explicit and deterministic.
- Home Assistant registries are not mutated by repair.
- Physical safety remains in canonical/native Red Queen execution.

## Release freeze

RC14 source is frozen. The remaining candidate gate is immutable exact-package
requalification of this frozen integration source. After that pass, only release-record
documentation outside the immutable integration package may change before
main/tag/prerelease publication.
