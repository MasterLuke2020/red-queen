# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0`
- Status: **FINAL EXACT PACKAGE LIVE VERIFIED — READY FOR PUBLICATION**
- Channel: `stable`
- Candidate: none
- Candidate status: `stable`

## Technical compatibility

- Home Assistant domain: `wnhf`
- Canonical execution service: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11`
- Development baseline: WNHF `1.40.0` / `WP-4.7.20.0`

## Verified release surface

- 8 capability definitions.
- 23 semantic actions.
- 16 canonical real-execution contracts.
- 68 Home Assistant services.
- Managed configuration remains ownership-gated and transaction-safe.
- Manual registries remain read-only until explicitly accepted migration.
- Manual → managed adoption is source-SHA guarded and backup-first.
- Guided repair is restricted to deterministic managed-registry cases.
- Semantic IDs remain stable through repair.
- Stale migration/repair writes fail closed.
- Home Assistant registries are not mutated by guided repair.
- `garage.stop` and all physical controls remain behind canonical guarded execution.

## Stable functional qualification

PASS:

- completely clean Home Assistant installation;
- managed commissioning and generated dashboard;
- diagnostics and Migration & Repair;
- exact RC14 → 1.0.0 upgrade preserving `/config/wnhf`;
- restart persistence;
- registry recovery/fail-closed behavior;
- config-entry remove/re-add preserving semantic data and dashboard storage;
- clean runtime checks on fresh and upgraded installations.

## HACS qualification

PASS:

- public HACS-addressable repository;
- root `hacs.json`;
- local Red Queen brand assets;
- Static repository checks after HACS activation;
- Home Assistant hassfest after HACS activation;
- real HACS clean installation;
- HACS redownload/reinstall;
- installed identity remained Red Queen `1.0.0` stable;
- `/config/wnhf` remained byte-identical through HACS redownload.

During qualification HACS first attempted a short-SHA archive URL and received HTTP
404, then completed its file-by-file fallback. The installed integration was complete
and correct both times. This is recorded as HACS client behavior, not a Red Queen
runtime failure.

## Final exact-package qualification

PASS on 2026-09-24.

Frozen integration source commit:

`21f2f948d2bd44c9d4723afd316b30dacc4a0aa3`

Final immutable package:

- Archive: `red_queen_1.0.0.zip`
- Integration files: `184`
- Size: `443865` bytes
- SHA-256:
  `dde35ba7a2139689ca8868e0572227da80ecaead2523c226d7cd3548c487299a`

Exact-package verification passed:

- package SHA-256 matched before installation;
- archive contained exactly 184 integration files;
- no packaged `__pycache__`;
- embedded identity was `1.0.0 / stable / stable / candidate null`;
- `candidate_status` was `stable`;
- only `custom_components/wnhf` was replaced;
- `/config/wnhf` was byte-identical before first startup;
- Home Assistant returned HTTP 200 after installation;
- semantic Registry remained byte-identical;
- entire `/config/wnhf` tree remained byte-identical after startup;
- restart persistence passed with the Registry and `/config/wnhf` still unchanged;
- managed/valid Red Queen configuration and `/red-queen` dashboard passed UI check;
- no Red Queen traceback, exception or runtime error was observed.

The integration source was not changed after the frozen package was built.

## Remaining publication gate

Only release publication steps remain:

1. commit these root-only qualification records;
2. run final repository CI on that root-only record commit;
3. fast-forward `main`;
4. restore `main` as repository default branch;
5. create annotated tag `v1.0.0`;
6. publish the non-prerelease GitHub release with the exact qualified ZIP.
