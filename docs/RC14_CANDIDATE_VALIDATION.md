# RC14 Candidate Validation

## Current state

**WP14.1 LIVE QUALIFIED — READ-ONLY PREVIEW COMPLETE**

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

## Qualification status

**WP14.1 COMPLETE.**

The read-only migration/repair preview has passed repository verification, hassfest,
static CI and both managed/manual live qualification cases. RC14 may proceed to an
explicitly confirmed migration transaction work package. No migration write path has
been live-qualified yet.
