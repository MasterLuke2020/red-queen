# Roadmap

The roadmap is directional rather than a promise of exact release numbers or dates.

## 1.0 release-candidate line

### Managed configuration and commissioning — completed in RC11

RC11 added explicit registry ownership modes and the transaction-safe Managed
configuration path.

### Generated Dashboard Foundation — completed in RC12

RC12 added the integration-owned native Home Assistant dashboard generated from the
semantic house model and native Red Queen entity surface.

### Managed maintenance and production diagnostics — completed in RC13

RC13 completed day-two managed maintenance, Entity/Provider diagnostics and dashboard
freshness/reload hardening.

### Controlled migration and repair — completed in RC14

RC14 completed read-only Migration & Repair preview, source-SHA guarded manual →
managed adoption, mandatory backups and guided repair.

## STABLE 1.0

Red Queen `1.0.0` has passed the functional and HACS qualification gates.

Completed:

- clean fresh installation and managed commissioning;
- RC14 → stable upgrade;
- restart persistence;
- recovery/fail-closed behavior;
- config-entry remove/re-add;
- clean runtime checks;
- HACS metadata/brand activation;
- real HACS clean install and redownload while preserving `/config/wnhf`.

The remaining 1.0 work is release engineering only: stable source freeze, immutable
exact-package qualification and final `v1.0.0` publication.

## Beyond 1.0

Climate, media and larger Plant Care expansions remain deferred until after 1.0.
