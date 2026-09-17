# Release Status

## Current candidate

**Red Queen 1.0.0-rc13 — FEATURE LIVE VERIFIED / RELEASE FREEZE**

RC13 advances the development lineage to WNHF `1.39.0` / `WP-4.7.19.0` and hardens
managed commissioning, maintenance, diagnostics and dashboard freshness.

## RC13 live qualification

The exact post-fix candidate was LIVE VERIFIED on the dedicated Home Assistant test
instance on 2026-09-17.

Reference candidate:

- Commit: `4f35dd96ed9254ca49cc86f0d27d5ead025c24d9`
- Integration files: `177`
- Package SHA-256:
  `bf43dcfb770f35e4fa93dba23b36a8d2667813459e93130f6cf174ed1bf1c7c5`

PASS results included managed commissioning; representative object creation/editing;
enable/disable; guarded deletion; dependent-room deletion protection; diagnostics
with 21 references, 21 ready and 0 findings; dashboard source freshness and update;
the fixed dashboard Options Flow completion; and restart persistence.

## Compatibility and safety

- Home Assistant integration domain remains `wnhf`.
- Canonical execution entry remains `wnhf.execution_execute`.
- Canonical execution API remains `1.0`.
- Canonical real-execution contract remains `2.3-rc11`.
- 8 capabilities, 23 semantic actions, 16 canonical real contracts and 68 services.
- Manual registries remain read-only and are never silently adopted.
- Physical safety remains in canonical/native Red Queen execution.

## Remaining RC13 publication gate

The release-freeze commit changes metadata/documentation and therefore requires one
final immutable package build from the frozen integration source. That exact package
receives a short startup/dashboard/diagnostics/restart requalification before the
final root-only qualification record, tag and GitHub prerelease.
