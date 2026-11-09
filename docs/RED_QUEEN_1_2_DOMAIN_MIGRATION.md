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
- [x] Opt-in synthetic night-OFF reconciliation and explicit manual ON pause
  implemented; **real-house staging and physical acceptance still pending**
- [x] Operator confirmed Straße Up/Down physical entity:
  `light.hof_vorplatz_red_queen_strasse_up_down`; legacy duplicate
  `light.wnhf_strasse_up_down` is unavailable (2026-11-09)
- [x] First real-house offline Restic staging: 245 entities, 36 devices,
  3,709 files, preserved legacy Stores and exact rollback-copy hashes
  (2026-11-09; NO HA boot or actual device tests)
- [ ] Read-only active-reference gate for existing real-house stage
- [ ] Hardware/network-isolated real-house HA boot, dashboard/script checks,
  hardware-negative tests and complete disaster-recovery acceptance
- [ ] Version \`1.2.0\`, immutable release artifact, HACS qualification and
  documented maintenance-window production acceptance

No checkbox above may be treated as satisfied merely by a successful
synthetic Home Assistant start. The current manifest remains 1.1.0 on purpose.


## Phase 1c: privacy-safe site reference inventory

The standalone tool \`tools/rq12_domain_reference_audit.py\` inventories YAML
and Lovelace configuration without exposing raw configuration values. It
identifies recognized legacy Home Assistant service calls, entity-ID references,
logger keys, old top-level integration keys, template/dynamic references, and
old/new Store key existence. Data is aggregated per relative file path and
category, with no secrets or full YAML/JSON contents printed.

Read-only example:

    python3 tools/rq12_domain_reference_audit.py --config /path/to/ha-config

**Important limitation:** This is a heuristic inventory and cannot detect all
third-party or remote consumers. A successful migration audit is not a live
deployment authorization. Service references are migrated only in explicitly
supported syntax; templates and unclassified dynamic references require manual
review. The synthetic old/new HA upgrade CI compares the auditor's reports so
the expected literal service references disappear while entity IDs remain stable.


## Phase 1d: five known site logger channels (isolated copy only)

The on-site read-only diagnostic identified **exactly eight** formerly
unclassified \`wnhf.*\` references: all are literal \`logger:\` values, not
Home Assistant services or entity identifiers:

- \`wnhf.channel_log\` (1)
- \`wnhf.channel_voice\` (2)
- \`wnhf.notify\` (3)
- \`wnhf.channel_router\` (1)
- \`wnhf.voice_driver\` (1)

The staging migration now converts **only these exact five recognized**
logging channel strings to their \`red_queen.*\` equivalents, preserving
quoting and comments. Any other/dynamic \`logger: wnhf.*\` aborts staging
rather than guessing. The reference inventory separately counts recognized
logger-channel mentions; unknown ones remain a manual-review blocker.
Synthetic unit and two-boot CI tests verify no legacy log channels survive
the staged copy and that entity IDs are untouched.

This is a narrow source-level migration. Only an isolated on-site stage
and subsequent HA package validation can confirm all real YAML structures
and runtime dependencies. No production files have been changed.

## 1.2 native scheduler safety additions (development)

At commit `6c167675`, the scheduler supports explicitly opted-in
`reconcile_missed_off` only for evening clock-based targeted OFF rules.
It never replays a scheduled ON at startup, checks the configured local
clock and sun position, and fails closed when sun is unavailable. It also
supports an optional `manual_pause_entity_id` input_boolean to suppress
scheduled ON without blocking OFF. Cross-rule actions are serialized.

The two Home Assistant 1.1-compatible fallback automations remain the
**only** proposed production lighting automation until Red Queen 1.2
passes real-site staging and hardware acceptance. **Never enable both**
the HA-native fallback and Red Queen native rules against the same lights.


## Explicit HA-native → Red Queen native lighting cutover gate

The operator confirmed the two HA 1.1-compatible sunset/23:00 automations
are already enabled and should remain in service until Red Queen 1.2 is
production-approved. The Red Queen 1.2 scheduler now contains a narrow
dispatch-time interlock: for scenes touching any of the three confirmed
outdoor lights, active/uncertain known HA fallback automation aliases
suppress native Red Queen dispatch. Other scenes stay unaffected.

Do **not** rely on alias matching for renamed automations. Required physical
handover order: validate all three circuits; record HA automation entity IDs;
confirm both fallback automations OFF; then explicitly activate only the
native Red Queen scene/rules and observe one sunset and 23:00 cycle. In a
rollback, disable the native rules first, restore known good HA fallback
configuration and then reactivate fallback automations. Never command the
same lights from both systems simultaneously.


## Phase 1e: offline site staging and independent recovery copy

The new \`tools/rq12_site_stage_preflight.py\` is an extra acceptance gate
for a **consistent restored backup** of the actual house HA configuration.
It requires explicit old-domain 245 entity / 36 device ownership counts,
presence and bytewise preservation of \`wnhf.dashboard\` and
\`wnhf.smart_living\`, unchanged legacy house registry files, unchanged
source-file hashes, private 0700 destination parents, and a separately
created byte-identical rollback copy. It rejects any source or destination
overlapping the supplied real productive HA config host mount.

The old-domain → new-domain two-boot synthetic CI now uses this same
site-style preflight rather than a bespoke shortcut. See
\`docs/RED_QUEEN_1_2_SITE_STAGING.md\` for requirements and commands.
This check **does not** start a stage containing real house credentials,
prove a live disaster recovery, merge anything, or release v1.2.0.


## Phase 1f: first real-house offline migration passed

Operator-supplied results from 2026-11-09: 245 entities, 36 devices,
3,709 files; the existing Dashboard and Smart Living Stores were preserved;
restored source unchanged and independent rollback copy byte-identical.
No HA instance was started with real credentials.

The newly added read-only site reference gate checks only the already
restored and staged directories, rejects remaining **active** old-domain
service/root/logger references, and distinguishes intentionally preserved
historical backup YAML. Real HA boot and production cutover remain blocked.
