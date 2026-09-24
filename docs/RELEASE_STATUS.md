# Release Status

## Current release

**Red Queen 1.0.0 — FINAL EXACT PACKAGE LIVE VERIFIED — READY FOR PUBLICATION**

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

## Final exact-package qualification

LIVE VERIFIED on 2026-09-24.

- Freeze commit:
  `21f2f948d2bd44c9d4723afd316b30dacc4a0aa3`
- Final archive: `red_queen_1.0.0.zip`
- Integration files: `184`
- Size: `443865` bytes
- SHA-256:
  `dde35ba7a2139689ca8868e0572227da80ecaead2523c226d7cd3548c487299a`

The exact package passed clean integration replacement, Home Assistant startup,
managed Registry preservation, complete `/config/wnhf` preservation, restart
persistence and Red Queen UI/dashboard checks. No Red Queen traceback, exception or
runtime error was observed.

The frozen integration source was not changed after packaging.

## Publication state

Ready for the final root-only record commit, final CI, `main` fast-forward, annotated
`v1.0.0` tag and non-prerelease GitHub Release using the exact qualified ZIP.
