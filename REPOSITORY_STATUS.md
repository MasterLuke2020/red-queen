# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0-rc7`
- Status: **LIVE VERIFIED / RELEASE PREPARATION READY**
- Channel: `release_candidate`
- Candidate: `rc7`

## Technical compatibility

- Home Assistant domain: `wnhf`
- Canonical execution service: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical dry-run contract: `1.8-rc7`
- Canonical real-execution contract: `1.9-rc7`
- Development baseline: WNHF `1.33.0` / `WP-4.7.13.2`

## Verified release surface

- 17 active domains; 2 planned domains.
- 7 capability definitions.
- 17 semantic actions.
- 11 canonical real-execution contracts.
- 66 Home Assistant services.
- Semantic Notifications Core remains compatible with the live-verified RC6 baseline.
- Native announcement and notification routing are live verified for RC7.
- Notification qualification is dispatch-scoped and does not claim delivery/read or
  hardware verification.
- Existing lighting, covers, openings/locks and garage contracts remain unchanged.

## Release preparation state

- Runtime source originated from the published, live-verified RC6 artifact.
- WP-4.7.13.2 adds native announcement and channel-routing code plus reference
  registry configuration.
- Static verification, isolated provider validation and reference-installation live
  validation passed.
- Repository owner: `MasterLuke2020`.
- Repository: `MasterLuke2020/red-queen`.
- Intended release after qualification: annotated tag `v1.0.0-rc7` and GitHub
  Pre-Release.
- HACS support remains intentionally inactive.
- Independent brand assets remain intentionally unresolved.

This document describes the live-verified RC7 candidate before release-branch
preparation and publication.
