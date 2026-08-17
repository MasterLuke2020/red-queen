# WNHF Canonical Execution Manager API v1.1

The Execution Manager separates four concepts: declared, semantically ready, real
execution enabled and executable now.

Current RC6 baseline: fifteen semantic actions across seven capabilities are declared.
Nine actions are enabled through `wnhf.execution_execute`: `lighting.turn_on`,
`lighting.turn_off`, `covers.open`, `covers.close`, `garage.open`,
`garage.close`, `openings.lock`, `openings.unlock` and
`notifications.send`.

Garage open/close and door lock/unlock require explicit confirmation. Notification
send requires no confirmation, requires a non-empty message and is non-idempotent.

`wnhf.execution_manager` and `wnhf.execution_action` are diagnostic services; they
do not dispatch actions themselves.
