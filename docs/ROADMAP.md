# Roadmap

The roadmap is directional rather than a promise of exact release numbers or dates.

## 1.0 release-candidate line

### Managed configuration and commissioning — completed in RC11

RC11 added explicit registry ownership modes and the transaction-safe
Managed configuration path.

### Generated Dashboard Foundation — completed in RC12

RC12 added the integration-owned native Home Assistant dashboard generated from the
semantic house model and native Red Queen entity surface.

### Managed maintenance and production diagnostics — RC13

RC13 completes the day-two Managed configuration foundation:

- transaction-safe edit/update while semantic IDs remain stable;
- managed enable/disable;
- guarded two-step deletion;
- dependent-room and last-room deletion protection;
- Entity/Provider diagnostics for explicitly configured references;
- dashboard freshness tracking against semantic registry source changes;
- reload-safe dashboard Options Flow completion.

RC13 is feature live verified and in release freeze.

## Next candidate

### Controlled migration and repair — RC14

RC14 is functionally live-qualified and in release freeze.

Completed scope:

- preview-only manual → managed migration planning;
- no automatic ownership takeover of manual registries;
- duplicate/invalid entity and orphan-room detection;
- source-SHA guarded explicit manual → managed adoption;
- mandatory source backup and rollback protection;
- deterministic guided entity-reference repair;
- deterministic HA area/floor source-link repair;
- stale-source fail-closed behavior.

## Stable 1.0 qualification

Stable `1.0.0` qualification is in its HACS/publication phase from the published RC14
baseline.

Fresh install, managed commissioning, RC14 → 1.0.0 upgrade, restart persistence,
recovery/fail-closed behavior, uninstall/reinstall and clean runtime gates have passed.
HACS metadata and local brand assets are now active for the final HACS installation and
update/reinstall qualification.

After the HACS gate, the remaining work is stable freeze, immutable exact-package
qualification and final `v1.0.0` publication. No new feature domain is planned for this
phase.

Climate, media and larger Plant Care expansions remain deferred until after 1.0.
