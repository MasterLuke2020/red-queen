# Publishing Checklist

## Stable 1.0 qualification setup

- [x] Start from published and exact-package-qualified RC14.
- [x] Create dedicated `release/1.0.0` branch.
- [x] Promote public version metadata to `1.0.0`.
- [x] Remove release-candidate label from stable runtime metadata.
- [x] Retain WNHF `1.40.0` / `WP-4.7.20.0`.
- [x] Keep canonical execution API `1.0`.
- [x] Keep canonical real-execution contract `2.3-rc11`.
- [x] Keep 8 capabilities, 23 semantic actions, 16 real contracts and 68 services.

## Functional stable qualification

- [x] Fresh install on a clean isolated Home Assistant instance.
- [x] Initial managed commissioning and generated dashboard.
- [x] Clean diagnostics and Migration & Repair.
- [x] Upgrade exact RC14 installation to stable 1.0.0 preserving `/config/wnhf`.
- [x] Managed ownership and semantic IDs survive upgrade.
- [x] Restart persistence.
- [x] Recovery/fail-closed behavior.
- [x] Uninstall/reinstall behavior.
- [x] Relevant runtime logs clean.

## HACS qualification

- [x] Activate root `hacs.json`.
- [x] Add local Red Queen brand icon assets.
- [x] Re-run static repository checks after HACS activation.
- [x] Re-run Home Assistant hassfest after HACS activation.
- [x] Make repository HACS-addressable.
- [x] Real HACS clean installation.
- [x] HACS redownload/reinstall behavior.
- [x] Confirm `/config/wnhf` survives HACS redownload byte-identically.

## Stable freeze/publication

- [x] Commit stable integration source freeze.
- [x] Regenerate `checksums/1.0.0_source.sha256` as part of freeze preparation.
- [x] Update public release documentation to stable 1.0.0 freeze state.
- [x] Static repository checks on exact freeze commit.
- [x] Home Assistant hassfest on exact freeze commit.
- [x] Build immutable `red_queen_1.0.0.zip`.
- [x] Exact-package live requalification.
- [x] Record final ZIP SHA-256 and qualification in root-only records.
- [ ] Commit root-only final qualification records.
- [ ] Final CI on root-only qualification record commit.
- [ ] Fast-forward `main`.
- [ ] Restore `main` as repository default branch.
- [ ] Create annotated tag `v1.0.0`.
- [ ] Publish non-prerelease GitHub release with exact qualified ZIP.

## Boundaries

- No new feature domains during stable qualification.
- Do not rename `wnhf`, public services, semantic IDs or persisted paths.
- Never silently adopt manual registries.
- Do not weaken physical feedback/confirmation guards.
- Climate, media and larger Plant Care remain deferred beyond 1.0.
