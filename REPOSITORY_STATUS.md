# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0`
- Status: **STABLE FREEZE — FUNCTIONAL/HACS LIVE VERIFIED**
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
404, then completed the supported file-by-file fallback. The installed integration was
complete and correct both times. This is recorded as HACS client behavior, not a Red
Queen runtime failure.

## Remaining publication gate

The integration source is ready to freeze. Remaining steps:

1. commit the stable source freeze;
2. run Static repository checks and hassfest on the exact freeze commit;
3. build deterministic `red_queen_1.0.0.zip` from that exact commit;
4. live-qualify that exact ZIP without changing the frozen integration afterward;
5. record the final ZIP SHA-256 in root-only release records;
6. fast-forward `main`, restore `main` as default branch, create annotated tag
   `v1.0.0`, and publish the non-prerelease GitHub release.
