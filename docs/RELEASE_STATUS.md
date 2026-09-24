# Release Status

## Current release

**Red Queen 1.0.0 — STABLE FREEZE — FUNCTIONAL/HACS LIVE VERIFIED**

Red Queen 1.0.0 promotes the live-qualified RC14 feature set to the first stable
release while retaining WNHF `1.40.0` / `WP-4.7.20.0`.

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

## Stable functional qualification

LIVE VERIFIED:

- clean fresh installation;
- managed commissioning and generated dashboard;
- RC14 → 1.0.0 upgrade preserving semantic data;
- restart persistence;
- fail-closed registry recovery and exact restoration;
- config-entry remove/re-add;
- clean runtime operation.

## HACS qualification

LIVE VERIFIED:

- HACS metadata and Red Queen brand assets;
- real HACS clean install;
- real HACS redownload/reinstall;
- version remained `1.0.0`, channel/phase remained `stable`;
- `/config/wnhf` and its Registry remained byte-identical.

A HACS short-SHA ZIP attempt returned HTTP 404 during both download tests; HACS then
completed its fallback download successfully. No Red Queen runtime error resulted.

## Final exact-package qualification

Pending after this stable source freeze.

The final package will be built deterministically from the exact freeze commit and
requalified on an isolated Home Assistant instance. The integration source must not be
changed after that package is built.
