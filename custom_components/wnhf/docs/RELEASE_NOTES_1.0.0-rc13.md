# Red Queen 1.0.0-rc13 — Development Notes

RC13 is the commissioning and maintenance hardening release on the path to Red Queen
1.0.0.

Development baseline:

- Red Queen `1.0.0-rc13`
- WNHF `1.39.0`
- `WP-4.7.19.0`
- Canonical execution API `1.0`
- Canonical real-execution contract `2.3-rc11`

## WP13.1 — Managed Maintenance Foundation

- Adds managed-object selection/read/update/delete primitives.
- Keeps semantic object IDs stable during maintenance.
- Adds transactional enable/disable.
- Prevents deletion of rooms that still own semantic child objects.
- Prevents deletion of the last managed room.
- Validates the complete candidate registry before every update/delete.
- Reuses existing backup/atomic-write/rollback infrastructure.
- Adds Configurator maintenance UI for rooms, lights, covers, openings and plants.
- Adds explicit delete confirmation.
- Adds German and English maintenance translations.
- Extends repository verification with managed-maintenance invariants.

This file describes an active development candidate. Exact-package live qualification
and publication status will be recorded only after RC13 feature freeze.

## WP13.2 — Production Diagnostics & Dashboard Freshness

- Adds Configurator entity/provider diagnostics.
- Classifies missing, disabled, unavailable, unknown and state-missing references.
- Shows integration/platform information where Home Assistant exposes it.
- Adds a post-maintenance dashboard-status reminder.
- Tracks generated dashboard freshness against the semantic registry source SHA.
- Keeps manual registries read-only.
- Keeps canonical physical execution semantics unchanged.

## WP13.2a — Dashboard OptionsFlow Completion Fix

- Fixes an `Invalid flow specified` popup after successful dashboard creation/update.
- Avoids unnecessary integration reloads for dashboard-only Options Flow actions.
- Adds explicit localized success results for dashboard create and update.
- Keeps normal Configurator registry-change reload behavior unchanged.
