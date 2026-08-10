# Canonical Execution Contract

## Public services

- Dry run / preflight: `wnhf.execution_dry_run`
- Real execution: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Real execution contract: `1.2-stage4.7.4`

## RC1 real-execution surface

Only `lighting.turn_off` is enabled for canonical real execution in RC1.

Action contract:

```text
action_id: lighting.turn_off
target_mode: single_object
required_target_keys: [object_id]
allowed_target_keys: [object_id]
allowed_parameter_keys: []
```

The action targets exactly one semantic light object.

## Readiness vocabulary

Red Queen deliberately distinguishes:

1. **declared** — semantic action definition exists;
2. **semantically_ready** — required providers resolve and are healthy/available;
3. **real_execution_enabled** — a canonical real-execution contract exists;
4. **executable_now** — both semantic readiness and real execution enablement are true.

At RC1, snapshot/validator actions can be semantically ready without being exposed as real canonical execution actions.

## Dry-run pipeline

```text
request
  ↓
action resolution
  ↓
canonical action-contract validation
  ↓
semantic target validation
  ↓
provider / technical-capability validation
  ↓
execution plan (dry_run=true)
```

Dry run never dispatches a hardware command.

## Real-execution pipeline

```text
validated request
  ↓
validation plan
  ↓
promotion to execution plan
  ↓
semantic router
  ↓
selected provider
  ↓
feedback guard / command dispatch
  ↓
effect confirmation
  ↓
qualification collector
```

## Verified toggle safety behavior

The RC1 reference action uses `guarded_momentary_pulse` for the test light.

If feedback already reports off:

```text
feedback OFF → no command → EXE-101 already_satisfied
```

If feedback reports on:

```text
feedback ON → one command pulse → feedback OFF confirmed → EXE-000 succeeded
```

The RC1 regression gate live-verified both paths.

## Confirmation

`lighting.turn_off` currently does not require explicit confirmation. Other/legacy execution surfaces may have different confirmation semantics. Qualification never bypasses confirmation policy.
