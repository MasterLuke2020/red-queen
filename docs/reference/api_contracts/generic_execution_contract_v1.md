# WNHF Canonical Execution Dry-Run Contract v1.1

`wnhf.execution_dry_run` is the non-mutating preflight for the canonical real
execution surface. It validates semantic/provider readiness, the action-specific
request envelope, the semantic target object, and provider technical capability.
It never dispatches a hardware command.

Current real-execution action contract:

```yaml
action: wnhf.execution_dry_run
data:
  action_id: lighting.turn_off
  target:
    object_id: light.eg.kitchen.spots
  parameters: {}
  confirmed: false
```

For `lighting.turn_off`, `target.object_id` is mandatory, exactly one semantic
light is targeted, no extra target keys are accepted, and parameters must be empty.
