# WNHF Canonical Execution Dry-Run Contract v1.1

`wnhf.execution_dry_run` is the non-mutating preflight for the canonical real
execution surface. It validates semantic/provider readiness, the action-specific
request envelope, the semantic target object, confirmation requirements and provider
technical capability. It never dispatches a command.

RC10 candidate real-execution-enabled actions are `lighting.turn_on`, `lighting.turn_off`,
`covers.open`, `covers.close`, `covers.blades_open`, `covers.blades_close`,
`garage.open`, `garage.close`, `openings.lock`, `openings.unlock`,
`openings.release`, `notifications.send`,
`notifications.announce`, `notifications.route` and `plants.record_watering`.
Every action requires exactly one `target.object_id`.

All physical-device action parameters must be empty. Every notification action
requires a non-empty string `message`. Direct send accepts `title`; announcement
accepts `level`; routing accepts `title`, `priority`, `profile`, `source` and
`category`. Unknown keys and unknown enum values are rejected.
Plant watering accepts no parameters.

Directional cover preflight blocks unavailable/contradictory feedback and opposite
movement. Blade preflight requires a healthy stable cover and an available configured
command entity. Door release additionally requires explicit confirmation and a proven
closed door. Garage and lock preflight enforce their confirmation and feedback guards.
Notification preflight reloads the semantic registry and validates notify entities,
TTS engines, speaker entities, Sonos native-announce dependencies and route context.
Plant Care preflight validates an enabled semantic plant and an available persistent
history store.
