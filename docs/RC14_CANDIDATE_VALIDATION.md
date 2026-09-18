# RC14 Candidate Validation

## Current state

**WP14.1 DEVELOPMENT — READ-ONLY PREVIEW IMPLEMENTED**

- Red Queen: `1.0.0-rc14`
- WNHF: `1.40.0`
- Work-package baseline: `WP-4.7.20.0`
- Theme: **Controlled Migration & Repair**
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11` (unchanged)

## Product boundary

RC14 is the final larger hardening candidate planned before stable 1.0. Its purpose is
to make existing installations safer to migrate and repair without silently taking
ownership of user-managed configuration.

The RC14 rules are:

- migration begins with preview only;
- a manual registry is never adopted automatically;
- every later mutation requires explicit user intent;
- backups are mandatory before accepted migration/repair writes;
- candidate registries must validate completely before replacement;
- physical execution contracts and guards remain unchanged.

## WP14.1 — Migration & Repair Preview Foundation

Implemented as a strictly read-only Configurator preview.

The preview reports current ownership mode and source validity, duplicate semantic IDs,
orphan-room references, malformed/incomplete object structures, full registry
validation failures, stored HA area/floor link problems and configured entity health.

It also computes a deterministic source bundle SHA-256, the proposed managed file set,
and migration eligibility. A manual source is eligible only when it is structurally
valid and has zero blockers.

Missing or HA-disabled entity references are blockers. Runtime-transient unavailable,
unknown or state-missing references are warnings.

The preview explicitly reports `write_performed: false`. It does not create an
ownership marker, rewrite registry YAML, mutate Home Assistant registries or dispatch
physical actions.

## Qualification status

Repository/static verification is the current WP14.1 gate. Live qualification and
all migration/repair write transactions remain future RC14 work packages.
