# Red Queen 1.0.0 — Stable Qualification

## Current state

**STABLE SOURCE FREEZE — FUNCTIONAL/HACS LIVE VERIFIED**

Baseline:

- Published predecessor: `v1.0.0-rc14`
- RC14 final commit: `2d89ba1b9fe514c86fe815a155d2b9e8cb70cff4`
- RC14 qualified ZIP SHA-256:
  `a30b91ae143dfb089795d623b45fd26483f9dc6bad0852374b6d0f8f1bc1ad98`
- Stable initialization commit:
  `4f96e4f70a0a307127c87eb0a9ea2e232e9a0a44`
- HACS activation / qualified source commit:
  `419dbe16dfb65d44dbf7691d69a6c4bac8876d3a`
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

## Functional qualification

PASS:

- Fresh installation on a completely clean isolated Home Assistant instance.
- Initial managed commissioning and generated dashboard.
- Clean diagnostics and Migration & Repair state.
- Exact RC14 → 1.0.0 upgrade preserving `/config/wnhf`.
- Managed ownership and semantic registry identity preserved across upgrade.
- Restart persistence on fresh and upgraded installations.
- Missing-registry recovery / fail-closed behavior.
- Recovery did not recreate or mutate missing/remaining registry files.
- Exact restoration returned the installation to normal operation.
- Config-entry uninstall/reinstall preserved `/config/wnhf` and dashboard storage.
- Clean runtime sanity checks on fresh and upgraded installations.

## HACS qualification

PASS:

- HACS metadata and local Red Queen brand assets active.
- Repository made public and HACS-addressable.
- Static repository checks after HACS activation: PASS.
- Home Assistant hassfest after HACS activation: PASS.
- Real HACS clean installation on an isolated Home Assistant instance: PASS.
- HACS installed Red Queen `1.0.0`, channel `stable`, phase `stable`,
  candidate `null`.
- HACS redownload/reinstall: PASS.
- Registry hashes remained byte-identical through HACS redownload.
- Entire `/config/wnhf` tree remained byte-identical through HACS redownload.
- Restart persistence after HACS commissioning: PASS.

Observed HACS client behavior:

- HACS first attempted `archive/refs/heads/419dbe1.zip` and received HTTP 404.
- HACS then completed its fallback file-by-file installation successfully.
- The same fallback occurred on redownload.
- The installed Red Queen integration was complete and correct after both operations.
- This is recorded as HACS client download behavior and did not produce a Red Queen
  runtime failure.

## Remaining qualification

1. Commit this stable source freeze.
2. Run Static repository checks and hassfest on the exact freeze commit.
3. Build immutable `red_queen_1.0.0.zip` from that exact commit.
4. Live-requalify that exact package.
5. Record final package SHA-256 in root-only release records.
6. Publish annotated `v1.0.0` as a non-prerelease GitHub release.

Climate, media and larger Plant Care expansion remain deferred beyond 1.0.
