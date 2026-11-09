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

## Phase 0.5: immutable-domain registry prototype (implemented, test-only)

The pure function in `tools/rq12_domain_registry_transform.py` transforms
offline *in-memory* registry objects to change only these ownership fields:

- HA config entry `domain`: `wnhf` → `red_queen`;
- HA entity platform `platform` for entities owned by that entry;
- HA device `identifiers` namespaces for that same entry.

It explicitly **does not rename** `entity_id`, `unique_id`, config entry IDs,
device IDs or user's settings. This preserves most dashboard references and
avoids disturbing third-party integrations with a legacy-looking display name.
The transform is not a migration runner; it has no filesystem write function,
and requires an independently verified stopped-HA cutover procedure.

Audit candidate entity-ID changes are now counted only for platform-owned
entities; third-party entities with a `wnhf_`-prefixed *user-visible name*
are reported separately. Entity-ID renaming is optional and out of scope
for the first domain cutover.

HA Store keys (`wnhf.smart_living`, `wnhf.dashboard`, future editor Store),
service namespace references in YAML/dashboard/scripts, and the HACS package
layout must be handled in separate, validated steps. Not covered by this
three-registry transform.

## Phase 1a: new integration package for synthetic HA boot (implemented)

The in-development package has moved to
\`custom_components/red_queen\` with manifest \`domain: red_queen\`
and the runtime \`DOMAIN\` constant changed coherently.

- HA service registration, smart-lighting semantic registry lookup, native
  dashboard service calls, and synthetic HA CI entry-point imports use the
  new domain.
- Original integration unique IDs (\`wnhf_*\`) and existing entity IDs remain
  untouched. Renaming them during a domain cutover would break dashboards.
- **Transitional data namespace** remains \`/config/wnhf\` with Store keys
  \`wnhf.smart_living\`, \`wnhf.dashboard\` and
  \`wnhf.smart_lighting_editor\`. This allows isolated package tests and
  preservation of manually configured settings; eventual data-key migration
  requires a separate, explicitly reversible phase.
- Python class names with \`WNHF\` remain internal implementation details.
  No WAGO output mapping, PLC logic, canonical object IDs, or DALI data was
  deliberately renamed.
- CI creates only a synthetic empty registry and must NOT run against the
  house server. It verifies package startup, basic editor/scheduler/semantic
  actions, and HA registry ownership. It is not a test of a real migrated
  \`wnhf\` config entry.

**Hard gate:** This package is NOT safe to install over Red Queen 1.1.0.
Production still contains an old-domain config entry; Home Assistant does
not automatically rewrite existing config-entry domain owners. The offline
pure transform is only a prototype. A separate coordinated offline
deployment tool must migrate all relevant persistence and references or
abort and restore the complete pre-cutover backup.

Test workflow changes apply only to this 1.2 experimental branch.

## HA 2026.9.2 device registry format verified by failed-closed test

The first synthetic old-installation boot exposed device records with
`identifiers: [["wnhf", ...]]` but **without a `config_entries` field**.
Our early migration guard correctly stopped instead of making assumptions.
The offline transform now accepts an **absent** association field only when
exactly one old-domain config entry exists and the old `wnhf` namespace is
owned by that entry. An explicitly **present but contradictory** association
still aborts the migration. The prototype reports `namespace_only_devices`
separately. Real site cutover remains blocked until the full upgrade smoke
test proves entity/device retention and staging of service references.


## Phase 1b: copy-only staging migration (implemented, not production)

\`tools/rq12_domain_stage.py\` accepts \`--source\`, \`--target\` and
\`--package\` and creates a **new** Home Assistant config directory. It refuses
existing destinations, nested source/destination paths, symlinks, mismatched
package domains, mixed/ambiguous HA domain registries, and inconsistent entity
identity. It never edits or deletes the source.

Changes are limited to the staged copy:

- Change HA config entry domain, Red Queen entity platform and owned device
  identifier namespace with the separately tested pure transform.
- Replace the old integration package by \`custom_components/red_queen\`.
- Rewrite only unambiguous **service call** references of the form
  \`wnhf.service_name\` in YAML \`service:\`/\`action:\` keys and Lovelace
  JSON \`service\`/\`action\` keys.
- Change an explicitly recognized top-level \`wnhf:\` YAML configuration key
  to \`red_queen:\`.
- Keep all existing \`light.wnhf_...\`, \`sensor.wnhf_...\` and other entity IDs,
  unique IDs, user configuration settings, previous dashboard ownership Store,
  Smart Living Store, and \`/config/wnhf\` data intact.
- Validate preserved config-entry, entity and device identity and output
  SHA-256 digests of before/after registry documents in a stage report.

User-authored YAML templates or unusual dashboard actions that cannot be
unambiguously recognized are a **manual-review blocker**: they may not be
silently rewritten. Do not interpret a clean stage as evidence that all
external automation consumers are covered.

Example **offline snapshot only**:

    python3 tools/rq12_domain_stage.py \
      --source /path/to/stopped-ha-backup-copy \
      --target /tmp/red-queen-12-stage \
      --package custom_components/red_queen

The target must not exist. The command does not start Home Assistant, change
production files, merge GitHub branches or activate house automations. The
original backup remains the rollback source; remove the stage directory to
discard an experimental migration. A production deployment will require a
separate, privileged, HA-stopped, guarded maintenance procedure.

## Red Queen 1.2 release checklist

- [x] Separate domain-migration development branch, parent Smart Lighting
  feature branch and protected production installation
- [x] Read-only on-site registry inventory (245 entities and 36 old namespace
  device identifiers reported; no name collisions in initial audit)
- [x] New integration package and registered Home Assistant domain
- [x] Strict offline registry ownership mapping; entity identity unchanged
- [x] Synthetic fresh-boot tests
- [x] Synthetic old-domain → new-domain two-boot migration fixture
- [ ] Validate the **copy-only stage tool** in the same two-boot CI workflow
- [ ] Diagnose all on-site custom dashboard/script calls including templates
  and unscanned external references
- [ ] Migrate persistent Store names and \`/config/wnhf\` data namespace with
  an explicit, verifiable recovery plan; this is separate from domain cutover
- [ ] User-visible WNHF naming cleanup without involuntary entity renames
- [ ] Missed night-time OFF policy after power loss/HA downtime and explicit
  manual override suppression
- [ ] Verify the **physical** Straße Up/Down canonical mapping before any
  automation is enabled
- [ ] Full sanitized-house staging with old dashboards, scripts, integrations,
  reboot, hardware-negative tests and restore verification
- [ ] Version \`1.2.0\`, immutable release artifact, HACS qualification and
  documented maintenance-window production acceptance

No checkbox above may be treated as satisfied merely by a successful
synthetic Home Assistant start. The current manifest remains 1.1.0 on purpose.
