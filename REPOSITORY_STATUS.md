# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0-rc8`
- Status: **LIVE VERIFIED**
- Channel: `release_candidate`
- Candidate: `rc8`

## Technical compatibility

- Home Assistant domain: `wnhf`
- Canonical execution service: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical dry-run contract: `1.9-rc8`
- Canonical real-execution contract: `2.0-rc8`
- Development baseline: WNHF `1.34.0` / `WP-4.7.14.0`

## Verified release surface

- 17 active domains; 2 planned domains.
- 7 capability definitions.
- 20 semantic actions.
- 14 canonical real-execution contracts.
- 66 Home Assistant services.
- Semantic Notifications Core remains compatible with the live-verified RC6 baseline.
- Native announcement and notification routing are live verified for RC7.
- Notification qualification is dispatch-scoped and does not claim delivery/read or
  hardware verification.
- RC8 adds dispatch-scoped cover blade execution and confirmed dispatch-scoped
  electric door release.
- Existing lighting, directional cover, openings/locks, garage and notification
  contracts remain unchanged.

## Release preparation state

- Runtime source originated from the published, live-verified RC7 artifact.
- WP-4.7.14.0 promotes existing blade and electric door-opener commands into the
  canonical execution surface.
- Static verification and isolated contract validation passed.
- Reference-installation blade and electric door-release live validation passed on
  2026-08-21 with final health 100, runtime ready and zero Red Queen errors or
  warnings.
- Repository owner: `MasterLuke2020`.
- Repository: `MasterLuke2020/red-queen`.
- Intended release after qualification: annotated tag `v1.0.0-rc8` and GitHub
  Pre-Release.
- HACS support remains intentionally inactive.
- Independent brand assets remain intentionally unresolved.

This document describes the live-verified RC8 candidate before release-branch
preparation and publication.
