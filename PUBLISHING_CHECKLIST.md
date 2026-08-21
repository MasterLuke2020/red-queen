# Publishing Checklist

## RC8 candidate preparation

- [x] Start from the live-verified
  `Red_Queen_1.0.0-rc7_Candidate_WP-4.7.13.2.zip` runtime source.
- [x] Promote blade-open and blade-close commands to canonical execution.
- [x] Add confirmed canonical electric door release.
- [x] Preserve all RC7 notification and existing physical-action contracts.
- [x] Update canonical contracts and RC8 documentation.
- [x] Add and verify `checksums/rc8_source.sha256`.
- [x] Build the replaceable Home Assistant test package.
- [x] Complete the controlled live-qualification plan on 2026-08-21.

## GitHub web release flow after live qualification

- [ ] Apply the verified RC8 source to the local repository checkout.
- [ ] Create `release/1.0.0-rc8` locally and commit intentionally.
- [ ] Push the release branch with Git.
- [ ] Confirm the static repository check passes.
- [ ] Confirm Home Assistant hassfest passes.
- [ ] Fast-forward `main` to the verified RC8 release commit.
- [ ] Create annotated tag `v1.0.0-rc8` on that exact commit.
- [ ] Create and publish GitHub Pre-Release `v1.0.0-rc8` in the web interface.
- [ ] Use `custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc8.md` as the
  release-note basis in the GitHub web interface.
- [ ] Record final commit, tag object and release artifact checksums.

## Compatibility and publication boundaries

- Do not rename the `wnhf` integration domain or `wnhf.*` service IDs.
- Do not modify the published RC1–RC7 tags or releases.
- Do not publish RC8 before blade and door-release live qualification passes.
- Do not claim blade position, latch release, physical door opening or hardware
  verification from dispatch-scoped success.
- Do not activate `hacs.json` until the independent publication requirements are
  deliberately completed.
- Do not use third-party franchise artwork, logos or character likenesses.
