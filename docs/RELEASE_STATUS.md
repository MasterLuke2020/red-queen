# Release Status

## Current candidate

**Red Queen 1.0.0-rc14 — FINAL EXACT PACKAGE LIVE VERIFIED**

RC14 advances the lineage to WNHF `1.40.0` / `WP-4.7.20.0` and completes the
controlled migration and guided repair hardening planned before stable 1.0.

## Functional live qualification

WP14.1, WP14.2 and WP14.3 passed isolated Home Assistant live qualification.

Coverage includes read-only migration/repair preview, manual registry blocker handling,
source-SHA fail-closed refusal, explicit manual → managed adoption, mandatory
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

## Final exact-package qualification

Freeze commit:
`5ec86514f96f88104a3531f669ca3d58b49910cb`

The frozen integration source was packaged and requalified without changing the
integration afterward.

- Integration files: `180`
- Final archive: `red_queen_1.0.0-rc14_final_candidate.zip`
- Final package SHA-256:
  `a30b91ae143dfb089795d623b45fd26483f9dc6bad0852374b6d0f8f1bc1ad98`
- Clean replacement: PASS
- Home Assistant startup / HTTP 200: PASS
- Managed registry load: PASS
- Entity/Provider diagnostics: 23/23 ready, 0 problems
- Migration & Repair: managed, source valid, 0 blockers, 0 warnings
- Generated dashboard: PASS
- Restart persistence: PASS
- Registry unchanged across restart: PASS
- Relevant Red Queen errors/tracebacks: none observed

The exact RC14 package is live-qualified. Only root-only release records may change
before tag/publication.
