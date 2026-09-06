# Red Queen 1.0.0-rc13 — Development Validation

Status: **WP13.1 DEVELOPMENT**

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
transaction backups and rollback behavior remain mandatory.

Room deletion is rejected while lights, covers, openings or plants still reference
the room, and the last managed room cannot be deleted.

## UI

The Options Flow exposes a dedicated **Manage objects** section for rooms, lights,
covers, openings and plants. Edit forms preserve the semantic ID, allow
enable/disable, and route deletion through a separate explicit confirmation step.

## Not changed

The canonical physical execution surface is unchanged in WP13.1.
`CANONICAL_EXECUTION_CONTRACT_VERSION` therefore remains `2.3-rc11`.
