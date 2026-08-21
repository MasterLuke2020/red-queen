# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0-rc9`
- Status: **LIVE VERIFIED**
- Channel: `release_candidate`
- Candidate: `rc9`

## Technical compatibility

- Home Assistant domain: `wnhf`
- Canonical execution service: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical dry-run contract: `2.0-rc9`
- Canonical real-execution contract: `2.1-rc9`
- Development baseline: WNHF `1.35.0` / `WP-4.7.15.0`

## Verified release surface

- Plant Care is an active release domain; climate and media remain planned.
- 8 capability definitions.
- 22 semantic actions.
- 15 canonical real-execution contracts.
- 67 Home Assistant services.
- Semantic Notifications Core remains compatible with the live-verified RC6 baseline.
- Native announcement and notification routing are live verified for RC7.
- Notification qualification is dispatch-scoped and does not claim delivery/read or
  hardware verification.
- RC9 adds optional semantic Plant Care, persistent watering history, dashboard
  sensors and canonical per-plant record-watering buttons without requiring
  soil-moisture hardware.
- Existing lighting, directional cover, openings/locks, garage and notification
  contracts remain unchanged.

## Release preparation state

- Runtime source originated from the published, live-verified RC7 artifact.
- WP-4.7.15.0 introduces Semantic Plant Care on the published RC8 baseline.
- Static verification and reference-installation live qualification passed on
  2026-08-21.
- Repository owner: `MasterLuke2020`.
- Repository: `MasterLuke2020/red-queen`.
- Intended release after qualification: annotated tag `v1.0.0-rc9` and GitHub
  Pre-Release.
- HACS support remains intentionally inactive.
- Independent brand assets remain intentionally unresolved.

This document describes the live-verified RC9 candidate before GitHub publication.
