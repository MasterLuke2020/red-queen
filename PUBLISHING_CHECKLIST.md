# Publishing Checklist

## RC13 candidate preparation

- [x] Start from published RC12.
- [x] Add managed maintenance for rooms, lights, covers, openings and plants.
- [x] Preserve stable semantic IDs during maintenance.
- [x] Add managed enable/disable and guarded two-step deletion.
- [x] Protect referenced rooms and the last managed room from deletion.
- [x] Add Entity/Provider diagnostics for configured references.
- [x] Add registry-source dashboard freshness tracking.
- [x] Fix and live-retest dashboard Options Flow completion.
- [x] Complete functional live qualification on the dedicated HA test instance.
- [x] Preserve 8 capabilities, 23 semantic actions, 16 canonical real contracts and
  68 Home Assistant services.
- [x] Keep canonical real-execution contract `2.3-rc11`.
- [x] Keep HACS metadata inactive.

## RC13 release freeze

- [x] Promote RC13 from development to release-candidate metadata.
- [x] Update public/integration documentation to RC13.
- [x] Regenerate `checksums/rc13_source.sha256`.
- [ ] Commit and push the freeze.
- [ ] Confirm static repository checks pass.
- [ ] Confirm Home Assistant hassfest passes.
- [ ] Build the final immutable RC13 integration ZIP.
- [ ] Record final ZIP SHA-256.
- [ ] Clean-replace the integration on the dedicated test instance.
- [ ] Verify startup, dashboard update and diagnostics from the exact final ZIP.
- [ ] Verify restart persistence from the exact final ZIP.
- [ ] Record exact-package qualification in root-only release documentation.

## GitHub web release flow

- [ ] Fast-forward `main` to the final RC13 release commit.
- [ ] Create annotated tag `v1.0.0-rc13` on that exact commit.
- [ ] Publish GitHub Pre-Release `v1.0.0-rc13` using
  `custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc13.md`.
- [ ] Attach the exact qualified RC13 ZIP to the release.

## Boundaries

- Do not rename the `wnhf` domain, public services, semantic IDs or persisted paths.
- Do not silently adopt or rewrite a manual registry.
- Do not weaken physical feedback/confirmation guards.
- Keep climate/media expansion deferred.
- Keep HACS metadata inactive for RC13.
