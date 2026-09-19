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
- [ ] Commit and push the freeze.
- [ ] Confirm static repository checks pass.
- [ ] Confirm Home Assistant hassfest passes.
- [ ] Build the final immutable RC14 integration ZIP.
- [ ] Record final ZIP SHA-256.
- [ ] Clean-replace the integration on the dedicated test instance.
- [ ] Verify startup, managed registry, Migration & Repair and diagnostics from the exact ZIP.
- [ ] Verify restart persistence from the exact ZIP.
- [ ] Record exact-package qualification in root-only release documentation.

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
