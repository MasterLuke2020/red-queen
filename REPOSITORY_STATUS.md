# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0-rc12`
- Status: **EXACT PACKAGE LIVE VERIFIED / REPOSITORY CI PENDING**
- Channel: `release_candidate`
- Candidate: `rc12`

## Technical compatibility

- Home Assistant domain: `wnhf`
- Canonical execution service: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11` (unchanged in RC12)
- Development baseline: WNHF `1.38.0` / `WP-4.7.18.0`

## Verified release surface

- 8 capability definitions.
- 23 semantic actions.
- 16 canonical real-execution contracts.
- 68 Home Assistant services.
- RC11 managed configuration/commissioning remains the semantic configuration base.
- RC12 adds an integration-owned generated native Home Assistant dashboard.
- Dashboard binding resolves current entity IDs by stable Red Queen unique IDs.
- Dashboard creation/update is explicit; restart restore is non-destructive.
- Manual registries remain read-only but can use the generated dashboard.
- `garage.stop` and all other physical controls continue to route through canonical
  guarded execution.

## RC12 exact-package qualification

On the dedicated Home Assistant test instance on 2026-08-24, the exact candidate
package with 174 integration files and SHA-256
`88b31e2da46ab052ba08c71f8600160f1a51e7719e0284597dee1eda249a02b0`
passed:

- fresh integration installation and startup;
- manual reference-registry loading and validation;
- dashboard preview with `168/168` expected native entity bindings and 0 issues;
- explicit dashboard creation at `/red-queen`;
- overview, floor, room, Plant Care and System/Diagnostics navigation;
- semantic unavailable-state rendering for intentionally absent providers;
- full Home Assistant restart with immediate dashboard persistence;
- post-restart dashboard state `Status: aktuell`;
- no Red Queen dashboard traceback/error and no oversized Recorder attribute warning.

## Remaining release gate

- Commit and push the frozen RC12 release candidate source.
- Pass repository static checks and Home Assistant hassfest on the release branch.
- Fast-forward `main`, create annotated tag `v1.0.0-rc12`, and publish the prerelease.

Repository owner: `MasterLuke2020`
Repository: `MasterLuke2020/red-queen`
Intended tag: `v1.0.0-rc12`
HACS metadata remains intentionally inactive.
