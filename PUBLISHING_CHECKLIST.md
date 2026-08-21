# Publishing Checklist

## RC10 candidate preparation

- [x] Start from the published, live-verified RC9 source.
- [x] Add native room state for every enabled opening.
- [x] Add native lock, door-release, garage and explicit blade controls.
- [x] Route native productive controls through canonical execution.
- [x] Preserve 8 capabilities, 22 semantic actions, 15 canonical real contracts and
  67 Home Assistant services.
- [x] Add and verify `checksums/rc10_source.sha256`.
- [x] Build the replaceable Home Assistant test package.
- [x] Complete controlled reference-installation live qualification.

## GitHub web release flow

- [ ] Apply the verified RC10 source to the local repository checkout.
- [ ] Create `release/1.0.0-rc10` locally and commit intentionally.
- [ ] Push the release branch with Git.
- [ ] Confirm static repository checks and hassfest pass.
- [ ] Fast-forward `main` to the verified RC10 release commit.
- [ ] Create annotated tag `v1.0.0-rc10` on that exact commit.
- [ ] Publish GitHub Pre-Release `v1.0.0-rc10` using
  `custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc10.md`.
- [ ] Record final commit, tag object and release artifact checksums.

## Boundaries

- Do not rename the `wnhf` domain, public services, semantic IDs or persisted paths.
- Do not publish RC10 before native-room live qualification and restart regression.
- Do not claim blade position, latch release, physical opening or unobserved garage
  direction.
- Keep central health/security/aggregate diagnostics central.
- Keep climate deferred and HACS metadata inactive.
