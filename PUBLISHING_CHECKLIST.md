# Publishing Checklist

This repository is deliberately **not yet publication-finalized**. Complete every item below before making it public.

## Required decisions

- [x] GitHub owner/repository: `MasterLuke2020/red-queen`.
- [x] MIT license selected and `LICENSE` added.
- [x] Maintainer/codeowner: `@MasterLuke2020`.
- [x] Issues: GitHub Issues; security reports: GitHub Private Vulnerability Reporting / Security Advisories when enabled.
- [ ] Create independent Red Queen brand assets. Do not use third-party franchise artwork, logos, character likenesses, or other borrowed branding.

## Home Assistant manifest

Update `custom_components/wnhf/manifest.json` only after the final repository URL exists:

- [x] `documentation`: `https://github.com/MasterLuke2020/red-queen#readme`.
- [x] `issue_tracker`: `https://github.com/MasterLuke2020/red-queen/issues`.
- [x] `codeowners`: `@MasterLuke2020`.
- [ ] Let GitHub Actions run hassfest after the first private push.

The technical domain remains `wnhf`.

## GitHub repository

- [x] Recommended description recorded in `GITHUB_SETUP.md`.
- [x] Recommended repository topics recorded in `GITHUB_SETUP.md`.
- [x] MIT license added.
- [ ] Configure issue/discussion/security settings.
- [ ] Enable branch protection as desired.
- [x] Hassfest workflow activated as `.github/workflows/hassfest.yml`.

## Optional HACS publication

HACS is not enabled in this preparation snapshot. If desired:

- [ ] Complete all manifest metadata above.
- [ ] Add an independent `brand/` asset set including at least `icon.png` in the location required by current Home Assistant/HACS guidance.
- [ ] Review `hacs.json.example`, then rename it to `hacs.json` only when ready.
- [ ] Decide/test the minimum supported Home Assistant version before adding a `homeassistant` constraint.
- [ ] Activate `tools/templates/hacs-validation.yml` as a workflow.
- [ ] Validate the repository with the HACS repository validator.

## RC1 publishing

- [ ] Tag the exact verified source as `1.0.0-rc1`.
- [ ] Create a GitHub Release (not just a tag) if using GitHub releases for distribution.
- [ ] Attach or archive the already verified runtime artifact `Red_Queen_1.0.0-rc1.zip` without rebuilding it silently.
- [ ] Publish the RC1 release notes from `docs/RELEASE_NOTES_1.0.0-rc1.md`.
- [ ] Verify the published artifact SHA-256 against `checksums/release_artifacts.sha256`.

## Do not do before 1.0 final

- Do not rename the `wnhf` integration domain or `wnhf.*` service IDs.
- Do not add new canonical cover/climate/media/notification/garage execution to RC1.
- Do not modify the verified RC1 artifact in place.
