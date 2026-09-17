# Red Queen 1.0.0-rc14 — Development Validation

Status: **WP14.1 DEVELOPMENT**

Baseline: WNHF `1.40.0` / `WP-4.7.20.0`

## Theme

Controlled Migration & Repair.

RC14 starts from the published RC13 candidate and keeps the canonical execution API
`1.0` and canonical real-execution contract `2.3-rc11` unchanged.

## WP14.1 contract

The first RC14 work package is read-only and fail-closed.

It may inspect existing semantic registry files and Home Assistant registry/state
metadata in order to produce a migration/repair preview. It must not:

- create `configurator.yaml` ownership markers;
- rewrite a manual registry;
- mutate Home Assistant area/floor/entity registries;
- infer provider fallbacks;
- dispatch physical actions.

Preview output must distinguish findings from proposed changes and must identify any
condition that blocks safe migration.

## Planned findings

- duplicate semantic IDs;
- orphaned room references;
- missing/disabled/unavailable/unknown/state-missing configured entities;
- invalid area/floor references where stored;
- incomplete object configuration;
- migration-blocking validation errors.

## Safety boundary

Manual registries remain read-only until a later work package adds an explicit,
reviewed acceptance transaction with backup, full-candidate validation, atomic replace
and rollback.
