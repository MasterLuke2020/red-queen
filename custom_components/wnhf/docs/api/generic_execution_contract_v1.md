# WNHF Canonical Execution Dry-Run Contract v1.1

`wnhf.execution_dry_run` is the non-mutating preflight for the canonical real
execution surface. It validates semantic/provider readiness, the action-specific
request envelope, the semantic target object, confirmation requirements and provider
technical capability. It never dispatches a command.

RC6 real-execution-enabled actions are `lighting.turn_on`, `lighting.turn_off`,
`covers.open`, `covers.close`, `garage.open`, `garage.close`,
`openings.lock`, `openings.unlock` and `notifications.send`. Every action requires
exactly one `target.object_id`.

All hardware action parameters must be empty. `notifications.send` requires a
non-empty string `message`, accepts optional string/null `title` and rejects other
parameter keys.

Directional cover preflight blocks unavailable/contradictory feedback and opposite
movement. Garage and lock preflight enforce their confirmation and feedback guards.
Notification preflight reloads the semantic target registry and validates target and
Home Assistant notify-entity availability.
