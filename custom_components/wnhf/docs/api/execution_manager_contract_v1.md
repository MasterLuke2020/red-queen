# WNHF Canonical Execution Manager API v1.1

The Execution Manager separates four concepts: declared, semantically ready, real
execution enabled and executable now.

Current RC7 candidate baseline: seventeen semantic actions across seven capabilities
are declared. Eleven actions are enabled through `wnhf.execution_execute`:
`lighting.turn_on`,
`lighting.turn_off`, `covers.open`, `covers.close`, `garage.open`,
`garage.close`, `openings.lock`, `openings.unlock` and
`notifications.send`, `notifications.announce` and `notifications.route`.

Garage open/close and door lock/unlock require explicit confirmation. All three
notification actions require no confirmation, require a non-empty message and are
non-idempotent.

`wnhf.execution_manager` and `wnhf.execution_action` are diagnostic services; they
do not dispatch actions themselves.
