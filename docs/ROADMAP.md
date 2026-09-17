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

RC14 is planned as the final larger hardening candidate before stable 1.0:

- preview-only manual → managed migration planning;
- never automatically take ownership of manual registries;
- duplicate/invalid entity and orphan-room detection;
- repair guidance for missing HA references and incomplete configuration;
- transaction-safe backup/rollback for explicitly accepted migration/repair.

## Stable 1.0 qualification

After RC14, stable qualification focuses on fresh install, upgrade, restart
persistence, recovery, uninstall/reinstall, clean logs, hassfest/static checks and the
final HACS installation flow rather than new feature domains.

Climate, media and larger Plant Care expansions remain deferred until after 1.0.
