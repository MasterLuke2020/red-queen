# Red Queen 1.0.0 — Stable Qualification

## Current state

**FINAL EXACT PACKAGE LIVE VERIFIED — READY FOR PUBLICATION**

Baseline:

- Published predecessor: `v1.0.0-rc14`
- RC14 final commit: `2d89ba1b9fe514c86fe815a155d2b9e8cb70cff4`
- RC14 qualified ZIP SHA-256:
  `a30b91ae143dfb089795d623b45fd26483f9dc6bad0852374b6d0f8f1bc1ad98`
- Stable initialization commit:
  `4f96e4f70a0a307127c87eb0a9ea2e232e9a0a44`
- HACS activation / qualified source commit:
  `419dbe16dfb65d44dbf7691d69a6c4bac8876d3a`
- Stable source freeze commit:
  `21f2f948d2bd44c9d4723afd316b30dacc4a0aa3`
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
- HACS then completed its file-by-file installation successfully.
- The same fallback occurred on redownload.
- The installed Red Queen integration was complete and correct after both operations.
- This did not produce a Red Queen runtime failure.

## Final exact-package qualification

PASS on 2026-09-24.

Frozen source:

`21f2f948d2bd44c9d4723afd316b30dacc4a0aa3`

Final package:

- `red_queen_1.0.0.zip`
- `184` integration files
- `443865` bytes
- SHA-256:
  `dde35ba7a2139689ca8868e0572227da80ecaead2523c226d7cd3548c487299a`

Qualification results:

- exact SHA-256 before installation: PASS;
- exact 184-file package shape: PASS;
- packaged `__pycache__`: none;
- embedded stable identity: PASS;
- `/config/wnhf` unchanged immediately after integration replacement: PASS;
- Home Assistant startup / HTTP 200: PASS;
- semantic Registry unchanged after startup: PASS;
- complete `/config/wnhf` tree unchanged after startup: PASS;
- restart persistence: PASS;
- semantic Registry unchanged after restart: PASS;
- complete `/config/wnhf` tree unchanged after restart: PASS;
- managed/valid configuration UI: PASS;
- generated `/red-queen` dashboard: PASS;
- Red Queen traceback/exception/runtime error: none observed.

The final ZIP is the release artifact. `custom_components/wnhf` must remain byte-identical
to the frozen source used to build it.

## Remaining publication

Only publication remains:

1. commit this root-only qualification record;
2. final CI on that record commit;
3. fast-forward `main`;
4. restore `main` as default branch;
5. create annotated `v1.0.0`;
6. publish the non-prerelease GitHub release with the exact qualified ZIP.

Climate, media and larger Plant Care expansion remain deferred beyond 1.0.
