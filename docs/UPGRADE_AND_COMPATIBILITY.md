# Upgrade and Compatibility

## Stable identity retained from WNHF

Red Queen 1.0 keeps these technical identities unchanged:

- integration domain: `wnhf`;
- service namespace: `wnhf.*`;
- configuration/persistence root: `/config/wnhf`;
- existing entity unique IDs;
- persistent canonical qualification evidence.

The public product name is Red Queen; WNHF is retained only where technical or historical compatibility requires it.

## Minimum schema metadata

RC1 reports minimum registry, decision and policy schema version `1.0` and `migration_required: false` for the verified baseline.

## Canonical vs legacy execution

New automations should use `wnhf.execution_execute`. Existing uses of `wnhf.execute` are a legacy compatibility path. Migration requires an intentional mapping from Decision ID semantics to canonical `action_id` + `target`; it is not a simple parameter rename.

## Upgrade practice during RC

For RC testing, use complete integration-directory replacement rather than mixing files from different work packages/candidates. Preserve `/config/wnhf` unless an explicit migration document says otherwise.

## Version line

The development lineage reached WNHF 1.27.0. The public release line restarts with semantic versioning at Red Queen `1.0.0-rc1`, followed by another RC only if defects require one, and then `1.0.0` when the candidate is accepted as stable.
