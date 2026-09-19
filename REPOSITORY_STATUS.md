# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0-rc14`
- Status: **FUNCTIONAL LIVE VERIFIED / RELEASE FREEZE**
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

## RC14 functional live qualification

WP14.1, WP14.2 and WP14.3 passed isolated Home Assistant live qualification.

PASS coverage includes read-only preview behavior, migration blocker detection,
source-SHA refusal, explicit manual → managed adoption, byte-faithful source backup,
restart ownership persistence, guided entity-reference repair, repair stale-source
refusal and guided HA area/floor-link repair.

## Remaining RC14 gate

RC14 source is frozen. Remaining work is immutable exact-package qualification followed
by final CI confirmation and the normal main/tag/prerelease publication flow.

Repository owner: `MasterLuke2020`
Repository: `MasterLuke2020/red-queen`
Intended tag: `v1.0.0-rc14`

HACS metadata remains intentionally inactive for the RC14 prerelease line.
