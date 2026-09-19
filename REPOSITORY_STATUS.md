# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0-rc14`
- Status: **FINAL EXACT PACKAGE LIVE VERIFIED**
- Channel: `release_candidate`
- Candidate: `rc14`

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

## RC14 functional qualification

WP14.1, WP14.2 and WP14.3 passed isolated Home Assistant live qualification, including
preview immutability, blocker detection, stale-source refusal, explicit manual adoption,
mandatory source backup, restart ownership persistence, guided entity repair and guided
HA area/floor-link repair.

## RC14 exact-package qualification

Frozen integration source commit:
`5ec86514f96f88104a3531f669ca3d58b49910cb`

Final immutable candidate:

- Integration files: `180`
- Archive: `red_queen_1.0.0-rc14_final_candidate.zip`
- SHA-256: `a30b91ae143dfb089795d623b45fd26483f9dc6bad0852374b6d0f8f1bc1ad98`

PASS results:

- clean integration replacement;
- Home Assistant startup / HTTP 200;
- managed registry loaded normally;
- diagnostics: 23 configured entity references / 23 ready / 0 problems;
- Migration & Repair: managed source valid, 0 blockers, 0 warnings;
- generated Red Queen dashboard loaded normally;
- restart persistence;
- registry files remained unchanged across restart;
- no Red Queen traceback or integration error was observed.

## Remaining publication gate

Only root release records changed after the frozen package qualification. The
integration package remains byte-identical to the qualified ZIP.

Remaining steps are final CI on the root-only release-record commit, fast-forwarding
`main`, creating tag `v1.0.0-rc14`, and publishing the GitHub prerelease with the exact
qualified ZIP.

Repository owner: `MasterLuke2020`
Repository: `MasterLuke2020/red-queen`
Intended tag: `v1.0.0-rc14`

HACS metadata remains intentionally inactive for the RC14 prerelease line.
