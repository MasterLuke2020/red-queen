# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0-rc13`
- Status: **FINAL EXACT PACKAGE LIVE VERIFIED / CI PASS**
- Channel: `release_candidate`
- Candidate: `rc13`

## Technical compatibility

- Home Assistant domain: `wnhf`
- Canonical execution service: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11` (unchanged in RC13)
- Development baseline: WNHF `1.39.0` / `WP-4.7.19.0`

## Verified release surface

- 8 capability definitions.
- 23 semantic actions.
- 16 canonical real-execution contracts.
- 68 Home Assistant services.
- Managed configuration remains ownership-gated and transaction-safe.
- Managed maintenance supports rooms, lights, covers, openings and plants.
- Semantic IDs remain stable during edits.
- Enable/disable and guarded deletion are supported.
- Entity/Provider diagnostics inspect only explicitly configured references.
- Generated-dashboard freshness tracks render and registry-source changes.
- Dashboard create/update is explicit; restart restore is non-destructive.
- Manual registries remain read-only.
- `garage.stop` and all physical controls remain behind canonical guarded execution.

## RC13 functional live qualification

The exact post-fix candidate at commit
`4f35dd96ed9254ca49cc86f0d27d5ead025c24d9` was live-tested on 2026-09-17.

PASS results included fresh managed commissioning, representative object
creation/maintenance, stable semantic identity, enable/disable, two-step deletion,
dependent-room deletion protection, diagnostics with 21/21 references ready and
0 findings, dashboard freshness/update, the dashboard Options Flow regression fix,
restart persistence and HTTP 200 after restart.

## RC13 exact-package qualification

The final immutable candidate contains `177` integration files and has
SHA-256 `a2d43bc3c4586d21caf7c275278980567449f0f94b75d11a4516c997f75f2b02`.

The exact package passed clean integration replacement, Home Assistant startup,
managed registry loading/validation, dashboard update, Entity/Provider diagnostics,
restart persistence and final HTTP reachability checks.

## Remaining RC13 publication gate

- Confirm CI/hassfest on the final root-documentation commit.
- Fast-forward `main` to that exact commit.
- Create annotated tag `v1.0.0-rc13`.
- Publish Red Queen `1.0.0-rc13` as a GitHub prerelease and attach the exact qualified ZIP.

Repository owner: `MasterLuke2020`
Repository: `MasterLuke2020/red-queen`
Intended tag: `v1.0.0-rc13`
HACS metadata remains intentionally inactive.
