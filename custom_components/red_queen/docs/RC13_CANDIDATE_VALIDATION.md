# Red Queen 1.0.0-rc13 — Candidate Validation

Status: **RELEASE FREEZE — FINAL EXACT PACKAGE REQUALIFICATION PENDING**

Baseline: WNHF `1.39.0` / `WP-4.7.19.0`

## Managed Maintenance contract

The Configurator may mutate registry objects only when `configurator.yaml` proves
Red Queen managed ownership. Manual registries remain read-only.

Maintenance operations:

- `object_options`
- `get_object`
- `update_object`
- `set_object_enabled`
- `delete_object`

Semantic object IDs are immutable during updates. Updates and deletions are validated
as a complete temporary house bundle before the live registry is replaced. Existing
transaction backups and rollback behavior remain mandatory. Referenced rooms and the
last managed room cannot be deleted.

## Production Diagnostics & Dashboard Freshness

`configuration_diagnostics.py` inspects only entity IDs explicitly configured in
the Red Queen registry. It does not scan arbitrary Home Assistant entities and does
not introduce provider fallback.

Dashboard lifecycle status receives the current registry source SHA. A source mismatch
marks the Red Queen-owned dashboard as outdated even if the visual render SHA did not
change.

## Dashboard Options Flow completion

The first RC13 live test exposed an `Invalid flow specified` popup after successful
dashboard creation. Dashboard create/update now terminate through a translated
`async_abort` result without an unnecessary integration reload.

## Functional live qualification — 2026-09-17

The exact post-fix candidate at commit
`4f35dd96ed9254ca49cc86f0d27d5ead025c24d9` passed managed commissioning,
representative object maintenance, enable/disable, guarded deletion, dependent-room
protection, dashboard freshness/update and restart persistence.

Entity/Provider diagnostics reported 21 configured references, 21 ready and 0 findings.

The release-freeze metadata/documentation change is non-runtime but changes package
bytes, so the frozen source receives one final exact-package requalification.
