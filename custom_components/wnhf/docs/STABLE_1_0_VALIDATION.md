# Red Queen 1.0.0 — Integration Stable Qualification

Status: **STABLE SOURCE FREEZE — FUNCTIONAL/HACS LIVE VERIFIED**

Stable 1.0 promotes the live-qualified RC14 feature set without adding a new feature
domain or changing the canonical physical execution contract.

- Version: `1.0.0`
- Channel: `stable`
- Phase: `stable`
- Release-candidate label: none
- WNHF baseline: `1.40.0`
- Work-package baseline: `WP-4.7.20.0`
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11`

Functional qualification passed for fresh installation, managed commissioning,
generated dashboard operation, RC14 upgrade, restart persistence, recovery/fail-closed
behavior, config-entry uninstall/reinstall and clean runtime operation.

HACS qualification also passed for clean installation and redownload/reinstall.
`/config/wnhf` remained byte-identical through HACS redownload.

During both HACS downloads the client first attempted a short-SHA branch archive and
received HTTP 404, then completed its file-by-file fallback successfully. The installed
Red Queen integration was complete and correct.

The remaining gate is immutable exact-package qualification from the stable freeze
commit. Integration source must not change after the final package is built.
