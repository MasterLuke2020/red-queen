# WNHF Public Access Execution API Contract v1.0

Status: **stable**

Compatibility policy: **additive only**

This contract applies to responses returned by:

```yaml
action: wnhf.access_object_execute
```

Clients may rely on every documented top-level field being present. A value may
be `null`, but a documented field is not removed or renamed within API contract
version `1.x`.

## Stable top-level fields

```yaml
api_contract:
result_code:
error_code:
execution_id:
generated_at:
finished_at:
duration_ms:

decision_id:
plan_id:

confirmed:
accepted:
state:
dry_run:
executed:
command_sent:
feedback_confirmed:

command_outcome:
effect_outcome:
transition_effect:
terminal_effect:

object_id:
step_id:
capability_snapshot:

capability:
command:
feedback_before:
feedback_after:
feedback_wait_ms:

reason:
error:
transitions:
blueprint:
versions:
```

## State

Possible values currently include:

- `created`
- `validating`
- `ready`
- `dispatching`
- `waiting_feedback`
- `observing_effect`
- `waiting_terminal_effect`
- `succeeded`
- `no_action`
- `rejected`
- `failed`

The returned top-level `state` is always terminal.

## Command outcome

```yaml
command_outcome:
  status: not_attempted | rejected | succeeded | failed
  attempted: boolean
  dispatched: boolean
  completed: boolean
  domain: string | null
  service: string | null
  entity_id: string | null
  message: string | null
```

This layer answers whether the technical command was accepted and completed by
the underlying platform call. It does not assert that the physical effect was
observed.

## Effect outcome

```yaml
effect_outcome:
  status: not_executed | not_required | not_observed | confirmed | failed
  required: boolean
  expected: string | null
  observed: string | null
  confirmed: boolean
  wait_ms: number
  message: string | null
```

`effect_outcome` is the canonical final effect. For multi-stage operations:

- `transition_effect` describes movement or transition start.
- `terminal_effect` describes the terminal target.
- `effect_outcome` mirrors the terminal effect.

For single-stage operations, `transition_effect` and `terminal_effect` are
present with value `null`.

## Capability snapshot

`capability_snapshot` is the immutable public view of the resolved capability
used for the execution:

```yaml
capability_snapshot:
  capability_id:
  object_id:
  provider:
    id:
    strategy:
  supported:
  available:
  healthy:
  confirmation_policy:
  command:
    domain:
    service:
    entity_id:
  feedback:
    required:
    entity_ids: []
  idempotency:
  rollback_supported:
```

The legacy `capability` and `command` fields remain available. New clients
should prefer `capability_snapshot`.

## Compatibility rules

Within API contract version `1.x`, WNHF may:

- add new fields
- add new enum values
- add new optional outcome objects
- provide more detailed messages

WNHF does not:

- remove documented fields
- rename documented fields
- change the meaning of existing boolean fields
- change a successful command into an implied physical-effect guarantee

A future breaking change requires a new major `api_contract` version.


## Result and error codes

Every response contains:

```yaml
result_code:
  code: ACC-000
  key: succeeded
  category: success
  severity: info
  retryable: false
  description: ...

error_code: null
```

`error_code` is `null` for success and no-action results. For rejected, failed
or internal results it repeats the stable compact code such as `ACC-205`.

Clients should branch on `result_code.code` or `result_code.key`, never on the
human-readable `reason` or `error` text.

The complete catalog is available through:

```yaml
action: wnhf.access_result_catalog
```
