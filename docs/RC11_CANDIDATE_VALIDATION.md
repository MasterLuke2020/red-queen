# RC11 Candidate Validation — WP-4.7.17.0

Status: **EXACT-PACKAGE LIVE VERIFIED — 2026-08-22**

## Candidate identity

- Red Queen `1.0.0-rc11`
- WNHF `1.37.0` / `WP-4.7.17.0`
- Canonical execution API `1.0`
- Canonical execution contract `2.3-rc11`
- 8 capabilities
- 23 semantic actions
- 16 canonical real actions
- 68 Home Assistant services

## Exact candidate package

The exact consolidated candidate package used for final live qualification had
SHA-256:

`9ad0f802d11dce56900323b1a50a1333f3d60d51e26e6522f404ceb7b6e7ce35`

The runtime integration source was then applied unchanged to the RC11 repository
branch; only repository/release metadata and verification tooling may change during
GitHub publication qualification.

## Managed configuration

PASS:

- managed registry status and validation;
- registry path `/config/wnhf/house/registry`;
- room creation from Home Assistant Area/Floor;
- automatic semantic room/object IDs;
- duplicate room/light rejection;
- managed light, cover, opening and Plant Care configuration;
- fresh commissioning/recovery after removal of the test `/config/wnhf` tree;
- persistence after Home Assistant restart.

## Native execution regression

PASS:

- impulse light off/on with objective feedback;
- venetian blind close/open with objective movement/end feedback;
- read-only cover position;
- blade commands while stationary and disabled/unavailable while moving;
- no arbitrary cover set-position UI;
- window and sliding-door state;
- door lock/unlock and electric release with open-door guard;
- garage open/close only from proven terminal states;
- ambiguous intermediate garage state blocks/hides direction;
- dedicated garage STOP is available only while objectively moving;
- STOP dispatches exactly one dedicated pulse and does not claim a resulting
  physical position;
- Plant Care record-watering persistence;
- optional moisture sensor remains metadata-only for RC11 care decisions;
- localized native/configuration guard messages.

## Restart regression

PASS:

- managed registry persisted;
- created room/object configuration persisted;
- representative native light, cover, door, garage and Plant Care entities returned;
- no functional RC11 regression was observed after the final restart.

## Repository publication gates

- [x] Exact-package Home Assistant live qualification.
- [x] `checksums/rc11_source.sha256` generated for the qualified integration source.
- [x] Release branch `release/1.0.0-rc11` created and pushed.
- [x] Home Assistant hassfest passed on 2026-08-23.
- [ ] Final repository static verification passes.
- [ ] Release-branch diff reviewed against published RC10.
- [ ] `main` fast-forwarded to the final release commit.
- [ ] Annotated tag `v1.0.0-rc11` created on that exact commit.
- [ ] GitHub Pre-Release published.

The initial RC11 static repository run correctly exposed that the repository verifier
and top-level release documentation still described RC10. This is repository
housekeeping, not a runtime integration defect; the live-qualified integration source
is intentionally left unchanged by the housekeeping patch.
