# Red Queen 1.0.0 — Stable Qualification

## Current state

**STABLE 1.0 QUALIFICATION — INITIALIZED**

Baseline:

- Published predecessor: `v1.0.0-rc14`
- RC14 final commit: `2d89ba1b9fe514c86fe815a155d2b9e8cb70cff4`
- RC14 qualified ZIP SHA-256:
  `a30b91ae143dfb089795d623b45fd26483f9dc6bad0852374b6d0f8f1bc1ad98`
- Stable target: `1.0.0`
- Home Assistant domain: `wnhf`
- WNHF baseline: `1.40.0`
- Work-package baseline: `WP-4.7.20.0`
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11`

Stable 1.0 is a promotion and qualification of the RC14 feature set, not a feature
expansion release.

Qualification gates:

1. Fresh install on a clean isolated Home Assistant instance.
2. RC14 → 1.0.0 upgrade while preserving `/config/wnhf`.
3. Restart and persistence.
4. Recovery/fail-closed behavior.
5. Uninstall/reinstall behavior.
6. Clean relevant logs plus static/hassfest validation.
7. HACS metadata activation and real HACS install/update flow.
8. Stable freeze and immutable exact-package qualification.

Climate, media and larger Plant Care expansion remain deferred beyond 1.0.
