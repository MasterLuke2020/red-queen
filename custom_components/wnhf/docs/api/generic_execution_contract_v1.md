# WNHF Canonical Execution Dry-Run Contract v1.1

`wnhf.execution_dry_run` is the non-mutating preflight for the canonical real
execution surface. It validates semantic/provider readiness, the action-specific
request envelope, the semantic target object, confirmation requirements, and provider
technical capability. It never dispatches a hardware command.

RC5 real-execution-enabled actions are `lighting.turn_on`, `lighting.turn_off`,
`covers.open`, `covers.close`, `garage.open`, `garage.close`, `openings.lock`, and
`openings.unlock`. Each requires exactly one `target.object_id`, accepts no extra
target keys, and accepts no parameters.

Directional cover preflight blocks unavailable/contradictory feedback and opposite
movement. Garage preflight requires explicit confirmation and a proven open/closed end
position; moving and intermediate positions are blocked. Lock/unlock preflight requires
explicit confirmation, a closed door contact, and stable lock feedback.
