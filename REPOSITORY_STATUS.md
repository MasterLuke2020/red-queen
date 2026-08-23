# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0-rc11`
- Status: **LIVE VERIFIED**
- Channel: `release_candidate`
- Candidate: `rc11`

## Technical compatibility

- Home Assistant domain: `wnhf`
- Canonical execution service: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical dry-run contract: `2.2-rc11`
- Canonical real-execution contract: `2.3-rc11`
- Development baseline: WNHF `1.37.0` / `WP-4.7.17.0`

## Verified release surface

- 8 capability definitions.
- 23 semantic actions.
- 16 canonical real-execution contracts.
- 68 Home Assistant services.
- Plant Care and Notifications remain active release domains.
- RC11 adds managed commissioning for rooms, lights, covers, openings and plants.
- Existing manual registries remain read-only.
- Managed writes are complete-bundle validated, staged, backed up and rolled back
  after write failure.
- `garage.stop` is canonical only when a dedicated STOP command exists and movement
  is objectively observed.
- Cover position remains read-only; blade position is never invented.
- Door lock/unlock and electric release remain closed-door guarded.
- Plant moisture input can be stored but does not drive RC11 watering state.

## Qualification

- RC11 was developed from the published, live-verified RC10 baseline.
- Exact-package live qualification passed on the dedicated Home Assistant test
  installation on 2026-08-22.
- Home Assistant hassfest passed on the RC11 release branch on 2026-08-23.
- Final repository static verification is required on the release commit before
  fast-forwarding `main`.
- Repository owner: `MasterLuke2020`.
- Repository: `MasterLuke2020/red-queen`.
- Intended tag: `v1.0.0-rc11`.
- HACS metadata remains intentionally inactive.

This document describes the live-verified RC11 candidate during GitHub publication
qualification.
