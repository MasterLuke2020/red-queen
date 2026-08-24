# Release Status

## Current candidate

**Red Queen 1.0.0-rc12 — FINAL EXACT PACKAGE LIVE VERIFIED / CI PASS**

RC12 advances the development lineage to WNHF `1.38.0` / `WP-4.7.18.0` and adds the
Generated Dashboard Foundation. Managed configuration from RC11 remains intact.

## RC12 exact-package qualification

The exact final RC12 candidate package was installed on a fresh dedicated Home
Assistant test instance and qualified on 2026-08-24.

Qualified package:

- Integration files: `174`
- SHA-256: `d1c683f56990ed14aa7e488564dad67d008fbd483ec3353ca793af56fec135d7`

Observed PASS results included:

- Red Queen `1.0.0-rc12` startup from the exact package;
- manual reference registry loaded and validated successfully;
- generated model for 3 floors, 23 rooms, 34 controllable lights, 17 covers,
  21 openings, 1 garage door and 13 plants;
- `168/168` expected native entity bindings resolved with 0 issues;
- explicit dashboard creation at `/red-queen`;
- overview, floor, room, Plant Care and System/Diagnostics navigation;
- semantic floor labels and unavailable-state handling;
- full Home Assistant restart with dashboard persistence;
- post-restart `Status: aktuell`;
- no Red Queen dashboard error/traceback and no oversized validation-sensor Recorder
  warning after restart.

Home Assistant hassfest required an explicit `lovelace` manifest dependency. After
that metadata-only correction, repository static checks and hassfest passed. The
rebuilt final package then passed targeted startup, dashboard restore and restart
persistence revalidation.

## Compatibility and safety

- Home Assistant integration domain remains `wnhf`.
- Canonical execution entry remains `wnhf.execution_execute`.
- Canonical execution API remains `1.0`.
- Canonical real-execution contract remains `2.3-rc11` (unchanged behavior).
- 8 capabilities, 23 semantic actions, 16 canonical real contracts and 68 services.
- Dashboard writes are explicit and isolated to the Red Queen-owned dashboard.
- Existing/default user dashboards are not rewritten.
- Physical safety remains in canonical/native Red Queen execution, not in Lovelace.

## Remaining RC12 publication gate

1. Fast-forward `main` to the verified release commit.
2. Create annotated tag `v1.0.0-rc12`.
3. Publish Red Queen `1.0.0-rc12` as a GitHub prerelease.
