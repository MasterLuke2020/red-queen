# Red Queen 1.0.0-rc14 — Development Validation

Status: **WP14.2 CONTROLLED MANUAL ADOPTION IMPLEMENTED**

Baseline: WNHF `1.40.0` / `WP-4.7.20.0`

## WP14.1 contract

`migration_repair.py` provides a deterministic read-only preview. Blocking registry
file I/O runs through Home Assistant's executor; HA area/floor/entity registries are
read on the event loop.

The preview detects structural migration blockers, duplicate IDs, orphan-room
references, incomplete managed-maintenance shapes, stored HA area/floor inconsistencies
and configured entity health problems. It returns proposed managed files and a source
bundle SHA-256 without persisting either.

`write_performed` is always false in WP14.1.

WP14.1 must not create `configurator.yaml`, rewrite registry files, mutate HA
registries, call managed update/delete/enable operations, infer provider fallback or
dispatch physical actions.

## Configurator

Both manual and managed registries expose **Migration & Repair**. For manual
registries the screen reports migration eligibility; for managed registries it acts
as read-only repair analysis. Closing the preview aborts without changing config-entry
options or requesting a reload.

## Next gate

Live-test preview behavior on a manual reference registry and on the managed test
registry before adding any accepted migration transaction.

## WP14.2 contract

Manual → managed adoption now requires an eligible preview and second confirmation.
It is source-SHA guarded, candidate-validated, backup-first, transactionally replaced
with rollback, and writes `configurator.yaml` last. Live qualification is pending.

## WP14.3 — Guided Repair

The Configurator can now guide deterministic repairs on a managed registry. Missing or
disabled configured entity references can be replaced with an explicitly selected
same-domain entity. Invalid stored HA area/floor metadata can be re-linked to a selected
HA area and its current floor assignment.

Repair selection is generated only from the production Migration & Repair findings.
The preview source SHA protects against stale writes, semantic IDs cannot change, the
complete candidate is validated through managed maintenance, and the existing
transaction path provides backup/rollback behavior.

Transient runtime states, duplicate IDs, orphan-room references and malformed objects
are deliberately not auto-repaired.
