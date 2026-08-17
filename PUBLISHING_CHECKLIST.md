# Publishing Checklist

## RC6 source preparation

- [x] Start from the live-verified
  `Red_Queen_1.0.0-rc6_Candidate_WP-4.7.13.1.zip` runtime source.
- [x] Update `SemanticExecutionManager.VERSION` to `1.6-rc6`.
- [x] Update RC6 repository and integration documentation.
- [x] Add the RC6 static repository verifier.
- [x] Add `checksums/rc6_source.sha256` with LF-normalized source hashes.
- [ ] Apply this branch-update package to `C:\Git\red-queen`.
- [ ] Run `python tools/verify_repository.py`.

## GitHub release flow

- [ ] Create/update the RC6 release branch from RC5 main commit
  `8d6990c9ebd13f7ecfa37c5f604581e8ce029ac9`.
- [ ] Commit the complete RC6 branch update intentionally.
- [ ] Push the release branch.
- [ ] Confirm the static repository check passes.
- [ ] Confirm Home Assistant hassfest passes.
- [ ] Fast-forward `main` to the verified RC6 release commit.
- [ ] Create annotated tag `v1.0.0-rc6` on that exact commit.
- [ ] Publish GitHub Pre-Release `v1.0.0-rc6`.
- [ ] Use `custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc6.md` as the
  release-note basis.
- [ ] Record final commit, tag object and release artifact checksums.

## Compatibility and publication boundaries

- Do not rename the `wnhf` integration domain or `wnhf.*` service IDs.
- Do not modify the published RC5 tag or release.
- Do not add notification announcements/TTS/routing to the RC6 core packet.
- Do not claim handset delivery/read or hardware verification for notification
  dispatch.
- Do not activate `hacs.json` until the independent publication requirements are
  deliberately completed.
- Do not use third-party franchise artwork, logos or character likenesses.
