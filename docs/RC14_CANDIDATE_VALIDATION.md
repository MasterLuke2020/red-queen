# RC14 Candidate Validation

## Current state

**WP14.2 LIVE QUALIFIED — CONTROLLED MANUAL ADOPTION COMPLETE**

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

## WP14.1 live qualification

WP14.1 is live-qualified on the isolated Home Assistant test environment.

### Managed registry case

- mode detected as `managed`;
- source registry valid;
- 9 configured Red Queen objects;
- 23 configured entity references / 23 ready;
- 0 blockers / 0 warnings;
- one informational `already_managed` finding;
- `write_performed: false`;
- registry SHA-256 set before/after preview was byte-identical;
- existing `configurator.yaml` remained byte-identical.

### Manual registry blocker case

The managed test registry was copied into a separate isolated HA instance and
`configurator.yaml` removed. Two configured light feedback references were then
deliberately changed to the nonexistent
`binary_sensor.rc14_missing_manual_test`.

Observed result:

- mode detected as `manual`;
- source registry remained structurally valid;
- 9 configured Red Queen objects;
- migration candidate: yes;
- migration eligible: no;
- 23 configured entity references / 21 ready;
- exactly 2 blockers;
- both blockers identified the two missing configured entity references;
- 0 warnings / 0 informational findings;
- `write_performed: false`;
- all five manual registry YAML files were byte-identical before/after preview;
- no `configurator.yaml` was created.

The UI formatting fix was also live-verified: finding sections now render with real
line breaks instead of literal `\\n` sequences.

## WP14.2 — Controlled Manual → Managed Adoption

Implemented after the live-qualified WP14.1 preview. Adoption requires an eligible
preview, a separate prepare action, and a second explicit confirmation. The preview
source SHA-256 is retained and rechecked before the write transaction.

The transaction refuses conflicting ownership markers, validates the complete
candidate, creates a mandatory backup of the manual source, stages all managed files,
writes `configurator.yaml` last, and rolls back already-replaced files on write
failure. The config entry is switched to managed mode only after success.

## WP14.2 live qualification

WP14.2 is live-qualified on the isolated manual-registry Home Assistant test instance.

### Source-SHA refusal case

An eligible manual preview was opened and its source SHA retained. Before the second
confirmation, `rooms.yaml` was deliberately changed without breaking YAML validity.

Observed result:

- Red Queen refused adoption with the source-changed message;
- no `configurator.yaml` was created;
- ownership remained manual;
- the original `rooms.yaml` was restored before the success case.

### Successful manual → managed adoption

The clean manual source was then adopted without modifying files between preview and
confirmation.

Observed result:

- `configurator.yaml` was created with `mode: managed`;
- owner is `red_queen_configurator`;
- managed files are `covers.yaml`, `lights.yaml`, `openings.yaml`, `plants.yaml`,
  and `rooms.yaml`;
- migration metadata records source mode `manual`;
- recorded source SHA-256:
  `d327e58c408322bba8ec4303682d842fdbf7c503369536fdf469182a648ca1b8`;
- a mandatory backup directory was created before adoption;
- the backup contains exactly the five original manual registry files;
- backup SHA-256 values matched the clean pre-migration manual baseline byte-for-byte.

### Restart / ownership persistence

After restarting the isolated Home Assistant test container, Red Queen still reported
registry mode `managed`. The full managed Configurator menu returned, including add and
object-maintenance actions.

## Qualification status

**WP14.1 COMPLETE. WP14.2 COMPLETE AND LIVE QUALIFIED.**

RC14 controlled migration now has live proof for read-only preview behavior, blocker
handling, source-SHA fail-closed refusal, explicit successful ownership transfer,
mandatory source backup, managed ownership persistence, and post-restart Configurator
availability. No physical execution contract changed.
