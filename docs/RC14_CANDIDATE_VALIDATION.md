# RC14 Candidate Validation

## Current state

**DEVELOPMENT — NOT YET A RELEASE CANDIDATE**

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
- every mutation requires explicit user intent;
- backups are mandatory before accepted migration/repair writes;
- candidate registries must validate completely before replacement;
- semantic IDs remain stable unless a migration explicitly creates a new managed
  identity from a reviewed source object;
- physical execution contracts and guards remain unchanged.

## WP14.1 — Migration & Repair Preview Foundation

The first work package is intentionally read-only.

Planned preview findings include:

- manual-registry ownership and migration eligibility;
- duplicate semantic IDs;
- objects referencing missing rooms;
- missing, disabled or otherwise invalid configured Home Assistant entity references;
- invalid/missing Home Assistant area/floor references where applicable;
- incomplete object configuration that cannot safely become managed;
- a deterministic proposed managed-registry result without writing it.

No migration or repair write operation belongs in WP14.1.

## Qualification status

No RC14 runtime feature has been implemented or live-qualified yet. The branch starts
from the published, exact-package-qualified RC13 commit.
