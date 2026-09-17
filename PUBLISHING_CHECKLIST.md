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
- [x] Commit and push the freeze.
- [x] Confirm static repository checks pass.
- [x] Confirm Home Assistant hassfest passes.
- [x] Build the final immutable RC13 integration ZIP.
- [x] Record final ZIP SHA-256.
- [x] Clean-replace the integration on the dedicated test instance.
- [x] Verify startup, dashboard update and diagnostics from the exact final ZIP.
- [x] Verify restart persistence from the exact final ZIP.
- [x] Record exact-package qualification in root-only release documentation.

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

## Final RC13 package identity

- Freeze source commit: `12437fbe50f3607f10fbf83401cdceee5764e94e`
- Integration files: `177`
- Archive: `red_queen_1.0.0-rc13_final_candidate.zip`
- SHA-256: `a2d43bc3c4586d21caf7c275278980567449f0f94b75d11a4516c997f75f2b02`
- Exact-package live qualification: **PASS**
