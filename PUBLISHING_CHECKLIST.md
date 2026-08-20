# Publishing Checklist

## RC7 verified-candidate preparation

- [x] Start from the live-verified
  `Red_Queen_1.0.0-rc6_Candidate_WP-4.7.13.1.zip` runtime source.
- [x] Implement native semantic announcement targets and notification routes.
- [x] Preserve direct `notifications.send` compatibility.
- [x] Port the historical profile, priority and context-routing semantics.
- [x] Update the canonical contracts and RC7 documentation.
- [x] Add and verify `checksums/rc7_source.sha256`.
- [x] Build the replaceable Home Assistant test package.
- [x] Complete the controlled live-qualification plan.

## GitHub web release flow after live qualification

- [ ] Apply the verified RC7 source to the local repository checkout.
- [ ] Create `release/1.0.0-rc7` locally and commit intentionally.
- [ ] Push the release branch with Git.
- [ ] Confirm the static repository check passes.
- [ ] Confirm Home Assistant hassfest passes.
- [ ] Fast-forward `main` to the verified RC7 release commit.
- [ ] Create annotated tag `v1.0.0-rc7` on that exact commit.
- [ ] Create and publish GitHub Pre-Release `v1.0.0-rc7` in the web interface.
- [ ] Use `custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc7.md` as the
  release-note basis in the GitHub web interface.
- [ ] Record final commit, tag object and release artifact checksums.

## Compatibility and publication boundaries

- Do not rename the `wnhf` integration domain or `wnhf.*` service IDs.
- Do not modify the published RC1–RC6 tags or releases.
- Do not publish RC7 before native announcement/routing live qualification passes.
- Do not depend on `script.notify_house` or the historical channel automations.
- Do not claim handset delivery/read or hardware verification for notification
  dispatch.
- Do not activate `hacs.json` until the independent publication requirements are
  deliberately completed.
- Do not use third-party franchise artwork, logos or character likenesses.
