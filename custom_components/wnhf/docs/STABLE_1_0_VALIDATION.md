# Red Queen 1.0.0 — Integration Stable Qualification

Status: **FUNCTIONAL GATES PASSED — HACS QUALIFICATION ACTIVE**

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

Functional qualification has passed for fresh installation, managed commissioning,
generated dashboard operation, RC14 upgrade, restart persistence, recovery/fail-closed
behavior, config-entry uninstall/reinstall and clean runtime operation.

The HACS qualification gate is now active. Stable source includes root HACS metadata
plus local 256x256 and 512x512 Home Assistant brand icons. Real HACS clean install and
HACS update/reinstall remain required before stable freeze/publication.
