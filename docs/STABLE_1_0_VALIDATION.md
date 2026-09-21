# Red Queen 1.0.0 — Stable Qualification

## Current state

**FUNCTIONAL STABLE GATES PASSED — HACS QUALIFICATION ACTIVE**

Baseline:

- Published predecessor: `v1.0.0-rc14`
- RC14 final commit: `2d89ba1b9fe514c86fe815a155d2b9e8cb70cff4`
- RC14 qualified ZIP SHA-256:
  `a30b91ae143dfb089795d623b45fd26483f9dc6bad0852374b6d0f8f1bc1ad98`
- Stable qualification source commit:
  `4f96e4f70a0a307127c87eb0a9ea2e232e9a0a44`
- Functional qualification ZIP:
  `red_queen_1.0.0_stable_qualification_candidate.zip`
- Functional qualification ZIP SHA-256:
  `5d6ceadcb8e26f0cb8f12b71c02f6d3a0ae1d6d6e110567c7a599b764ec26d75`
- Stable target: `1.0.0`
- Home Assistant domain: `wnhf`
- WNHF baseline: `1.40.0`
- Work-package baseline: `WP-4.7.20.0`
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11`

Stable 1.0 is a promotion and qualification of the RC14 feature set, not a feature
expansion release.

## Completed functional qualification

- Fresh installation on a completely clean isolated Home Assistant instance: PASS.
- Initial managed commissioning and generated dashboard: PASS.
- Clean diagnostics and Migration & Repair state: PASS.
- Exact RC14 → 1.0.0 upgrade preserving `/config/wnhf`: PASS.
- Managed ownership and semantic registry identity preserved across upgrade: PASS.
- Restart persistence on fresh and upgraded installations: PASS.
- Missing-registry recovery / fail-closed behavior: PASS.
- Recovery did not recreate or mutate missing/remaining registry files: PASS.
- Exact restoration returned the installation to normal operation: PASS.
- Config-entry uninstall/reinstall preserved `/config/wnhf` and managed dashboard storage: PASS.
- Clean runtime sanity checks on fresh and upgraded installations: PASS.
- Static repository checks and hassfest passed for the stable initialization commit.

## Active HACS qualification gate

The repository now carries the HACS metadata and local Home Assistant brand assets
required for the stable publication path:

- root `hacs.json`;
- `custom_components/wnhf/brand/icon.png` (256x256);
- `custom_components/wnhf/brand/icon@2x.png` (512x512).

The repository remains unpublished/private during this preparation step. Real HACS
installation, update/reinstall qualification, stable freeze, exact-package
requalification and final publication remain outstanding.

Climate, media and larger Plant Care expansion remain deferred beyond 1.0.
