# GitHub Repository Setup — Red Queen

## Repository identity

- Owner: `MasterLuke2020`
- Repository: `red-queen`
- Initial visibility: **Private**
- Default branch: `main`
- License: MIT
- Maintainer / codeowner: `@MasterLuke2020`

## Recommended GitHub description

> Semantic home intelligence framework for Home Assistant with context-aware decisions, capability/provider resolution, guarded execution and feedback-based qualification.

## Recommended topics

`home-assistant`, `smart-home`, `home-automation`, `semantic-home`, `automation-framework`, `python`

## Repository URLs

- Documentation: `https://github.com/MasterLuke2020/red-queen#readme`
- Issues: `https://github.com/MasterLuke2020/red-queen/issues`

## Initial repository settings

Create the repository empty: do **not** ask GitHub to generate a README, `.gitignore`, or license, because those files already exist in this source tree.

After the first push:

1. Keep the repository private while RC1 is in soak testing.
2. Confirm the default branch is `main`.
3. Check **Actions** and confirm `Red Queen static checks` and `Validate with hassfest` complete successfully.
4. Enable Issues.
5. Enable Private Vulnerability Reporting / Security Advisories before public release.
6. Do not activate HACS until independent brand assets and the HACS publication decision are complete.

## RC1 release rule

Do not rebuild or silently alter the verified `1.0.0-rc1` runtime artifact. Repository-only documentation or publication metadata changes must remain distinguishable from the archived live-verified release package.
