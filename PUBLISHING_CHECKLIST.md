# Publishing Checklist

## RC14 candidate preparation

- [x] Start from published RC13.
- [x] Add read-only Migration & Repair preview.
- [x] Detect migration blockers and configured entity/HA-link problems.
- [x] Add source-SHA guarded manual → managed adoption.
- [x] Require explicit prepare action and second confirmation.
- [x] Require mandatory source backup before adoption.
- [x] Add deterministic guided entity-reference repair.
- [x] Add deterministic HA area/floor source-link repair.
- [x] Preserve stable semantic IDs during repair.
- [x] Keep physical execution contract `2.3-rc11` unchanged.
- [x] Complete WP14.1 live qualification.
- [x] Complete WP14.2 live qualification.
- [x] Complete WP14.3 live qualification.
- [x] Preserve 8 capabilities, 23 semantic actions, 16 canonical real contracts and
  68 Home Assistant services.
- [x] Keep HACS metadata inactive.

## RC14 release freeze

- [x] Promote RC14 from development to release-candidate metadata.
- [x] Update public/integration documentation to RC14.
- [x] Regenerate `checksums/rc14_source.sha256`.
- [x] Commit and push the freeze.
- [x] Confirm static repository checks pass.
- [x] Confirm Home Assistant hassfest passes.
- [x] Build the final immutable RC14 integration ZIP.
- [x] Record final ZIP SHA-256.
- [x] Clean-replace the integration on the dedicated test instance.
- [x] Verify startup, managed registry, Migration & Repair and diagnostics from the exact ZIP.
- [x] Verify restart persistence from the exact ZIP.
- [x] Record exact-package qualification in root-only release documentation.

## GitHub web release flow

- [ ] Fast-forward `main` to the final RC14 release commit.
- [ ] Create annotated tag `v1.0.0-rc14` on that exact commit.
- [ ] Publish GitHub Pre-Release `v1.0.0-rc14` using
  `custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc14.md`.
- [ ] Attach the exact qualified RC14 ZIP to the release.

## Boundaries

- Do not rename the `wnhf` domain, public services, semantic IDs or persisted paths.
- Do not silently adopt or rewrite a manual registry.
- Do not auto-repair ambiguous structural findings or transient runtime states.
- Do not weaken physical feedback/confirmation guards.
- Keep climate/media expansion deferred.
- Keep HACS metadata inactive for RC14.


## Final RC14 package identity

- Freeze source commit: `5ec86514f96f88104a3531f669ca3d58b49910cb`
- Integration files: `180`
- Archive: `red_queen_1.0.0-rc14_final_candidate.zip`
- SHA-256: `a30b91ae143dfb089795d623b45fd26483f9dc6bad0852374b6d0f8f1bc1ad98`
- Exact-package live qualification: **PASS**
