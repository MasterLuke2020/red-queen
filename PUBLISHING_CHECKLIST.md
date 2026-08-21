# Publishing Checklist

## RC9 candidate preparation

- [x] Start from the published, live-verified RC8 source.
- [x] Add the optional 13-plant semantic registry.
- [x] Add persistent watering history, dashboard-ready plant sensors and native
  canonical record-watering buttons.
- [x] Add canonical `plants.record_watering` with state-scoped qualification.
- [x] Preserve all RC8 contracts.
- [x] Add and verify `checksums/rc9_source.sha256`.
- [x] Build the replaceable Home Assistant test package.
- [x] Complete the controlled live-qualification plan.

## GitHub web release flow

- [ ] Apply the verified RC9 source to the local repository checkout.
- [ ] Create `release/1.0.0-rc9` locally and commit intentionally.
- [ ] Push the release branch with Git.
- [ ] Confirm the static repository check passes.
- [ ] Confirm Home Assistant hassfest passes.
- [ ] Fast-forward `main` to the verified RC9 release commit.
- [ ] Create annotated tag `v1.0.0-rc9` on that exact commit.
- [ ] Create and publish GitHub Pre-Release `v1.0.0-rc9` in the web interface.
- [ ] Use `custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc9.md` as the
  release-note basis in the GitHub web interface.
- [ ] Record final commit, tag object and release artifact checksums.

## Compatibility and publication boundaries

- Do not rename the `wnhf` integration domain or `wnhf.*` service IDs.
- Do not modify the published RC1–RC7 tags or releases.
- Do not publish RC9 before Plant Care live qualification and restart persistence pass.
- Do not claim blade position, latch release, physical door opening or hardware
  verification from dispatch-scoped success.
- Do not activate `hacs.json` until the independent publication requirements are
  deliberately completed.
- Do not use third-party franchise artwork, logos or character likenesses.
