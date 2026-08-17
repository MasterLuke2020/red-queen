# Repository Status

## Product

- Name: **Red Queen**
- Version: `1.0.0-rc6`
- Status: **LIVE VERIFIED / PUBLICATION PENDING**
- Channel: `release_candidate`
- Candidate: `rc6`

## Technical compatibility

- Home Assistant domain: `wnhf`
- Canonical execution service: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical dry-run contract: `1.7-rc6`
- Canonical real-execution contract: `1.8-rc6`
- Verified development baseline: WNHF `1.32.0` / `WP-4.7.13.1`

## Verified release surface

- 17 active domains; 2 planned domains.
- 7 capability definitions.
- 15 semantic actions.
- 9 canonical real-execution contracts.
- 66 Home Assistant services.
- Semantic Notifications Core is active and live verified.
- Notification qualification is dispatch-scoped and does not claim delivery/read or
  hardware verification.
- Existing lighting, covers, openings/locks and garage contracts remain unchanged.

## Repository preparation state

- Runtime source originated from the live-verified RC6 candidate artifact.
- The only post-live runtime-source change is the internal
  `SemanticExecutionManager.VERSION` cleanup to `1.6-rc6`.
- RC6 documentation, verifier and LF-normalized source checksum catalogue are
  included.
- Repository owner: `MasterLuke2020`.
- Repository: `MasterLuke2020/red-queen`.
- Intended release: annotated tag `v1.0.0-rc6` and GitHub Pre-Release.
- HACS support remains intentionally inactive.
- Independent brand assets remain intentionally unresolved.

This document describes the RC6 release-branch package before CI, main
fast-forward, tagging and Pre-Release publication.
