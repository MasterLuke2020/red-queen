# Red Queen 1.2 — technical domain migration, phase 0

**State:** Read-only preflight committed on a separate development branch.
No active integration or configuration has been migrated.

## Decision

Target Home Assistant integration domain: **red_queen** (formerly **wnhf**).
The product has one known active home installation; there is no need to carry
an indefinite compatibility layer for other customers. Nevertheless, the
existing owner's production installation and references must survive migration.

The current 1.2 Smart Lighting work stays in its original feature branch
until this migration is validated and explicitly integrated.

## Phase 0: read-only inventory (implemented)

Run from a checkout of this branch against a preferably offline backup
of the HA /config directory:

    python3 tools/rq12_domain_migration_audit.py --config /path/to/config --strict

The command prints JSON only; it never changes files, registers entities,
calls services, or accesses a PLC. It identifies:

- existing wnhf/red_queen config entries in HA;
- registered entity platforms and config-entry associations;
- device identifiers that use the old domain;
- potential collisions when optional wnhf_* entity IDs are renamed;
- local HA automation/script/configuration/dashboard references;
- the presence of old and new Store namespaces and component directories.

Only recognized HA storage registries and selected automation/dashboard
source files are inspected; raw config-entry contents and secrets are not
printed. Counts are an impact estimate, not proof of a complete dependency
graph. In particular, external MQTT consumers, third-party integrations,
mobile widgets, and PLC source logic require separate inventory.

A clean report does NOT authorize production migration.

## Phase 1: isolated integration package and compatibility tests (planned)

- Move custom_components/wnhf to custom_components/red_queen;
  change manifest and runtime domain coherently, update imports and tools.
- Update HA services and unique identifiers only with explicit mapping.
  Keep object IDs and canonical PLC mappings stable.
- Move or transparently read the legacy /config/wnhf registry and Smart Living
  Store data in a controlled, versioned migration.
- Handle the old HA config entry, entity registry and device registry via
  supported HA APIs or an isolated verified offline migration. Never do a
  blind live search/replace in .storage.
- Inventory YAML, dashboard, script, automation and external references.
- Ensure HACS clean installation finds the new integration folder and
  no duplicate integration is loaded.
- Verify synthetic fresh install and synthetic migration from a real-like
  wnhf registry snapshot; test recovery, rollback, idempotency and restart.

## Phase 2: guarded production cutover (NOT authorized)

Required before deployment:
1. Full HA/config/wnhf backup and verifiable rollback, including .storage.
2. Read-only on-site impact report inspected, with entity-ID conflict resolution.
3. Passed unit tests, hassfest, isolated HA boot, migration roundtrip and
   real staging with the production-derived, sanitized registry.
4. Explicitly scheduled maintenance window, with control of the old/new
   integration to avoid double execution of any action.
5. Operator sign-off on the complete mapping of light, cover, door, garage,
   alarm, Smart Living scenes and external consumers.

**Prohibited:** editing production .storage while HA runs, activating
lighting automations during migration, changing WAGO PLC code, or deploying
an unqualified new domain alongside the active wnhf integration.

Rollback means restore the entire matched configuration snapshot and 1.1.0
integration package before restarting HA, not merely rename a directory.
