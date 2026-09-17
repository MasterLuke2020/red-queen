# Red Queen 1.0.0-rc13 — Release Candidate Notes

RC13 is the commissioning and maintenance hardening release on the path to Red Queen
1.0.0.

Release identity:

- Red Queen `1.0.0-rc13`
- WNHF `1.39.0`
- `WP-4.7.19.0`
- Canonical execution API `1.0`
- Canonical real-execution contract `2.3-rc11`

## Managed Maintenance

- Adds managed-object selection/read/update/delete primitives.
- Keeps semantic object IDs stable during maintenance.
- Adds transaction-safe enable/disable.
- Prevents deletion of referenced rooms and the last managed room.
- Validates the complete candidate registry before every update/delete.
- Reuses existing backup/atomic-write/rollback infrastructure.
- Adds Configurator maintenance UI for rooms, lights, covers, openings and plants.
- Adds explicit second confirmation before deletion.

## Production Diagnostics & Dashboard Freshness

- Adds Configurator Entity/Provider diagnostics.
- Classifies missing, disabled, unavailable, unknown and state-missing references.
- Skips intentionally disabled Red Queen objects.
- Tracks generated-dashboard freshness against the semantic registry source SHA.
- Keeps manual registries read-only.
- Keeps canonical physical execution semantics unchanged.

## Dashboard Flow Hardening

- Fixes an `Invalid flow specified` popup after successful dashboard creation/update.
- Avoids unnecessary integration reloads for dashboard-only Options Flow actions.
- Adds localized success completion for dashboard create and update.
- Keeps normal Configurator registry-change reload behavior unchanged.

## Live validation

The post-fix RC13 feature set was live-verified on 2026-09-17. Managed commissioning,
representative object maintenance, enable/disable, guarded deletion, diagnostics,
dashboard freshness/update and restart persistence passed. Diagnostics reported
21 configured references, 21 ready and 0 findings.

The frozen candidate receives one final exact-package requalification before GitHub
prerelease publication.

## Compatibility and safety

- Technical Home Assistant domain remains `wnhf`.
- Canonical execution service remains `wnhf.execution_execute`.
- Canonical execution API remains `1.0`.
- Canonical real-execution contract remains `2.3-rc11`.
- Physical safety/guard behavior is unchanged.
- Manual registries are never silently adopted.
- HACS metadata remains intentionally inactive for this prerelease.
