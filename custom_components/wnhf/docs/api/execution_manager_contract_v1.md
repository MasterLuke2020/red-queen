# WNHF Canonical Execution Manager API v1.1

The Execution Manager separates four concepts: declared, semantically ready, real
execution enabled and executable now.

Current RC8 candidate baseline: twenty semantic actions across seven capabilities
are declared. Fourteen actions are enabled through `wnhf.execution_execute`:
`lighting.turn_on`,
`lighting.turn_off`, `covers.open`, `covers.close`, `covers.blades_open`,
`covers.blades_close`, `garage.open`, `garage.close`, `openings.lock`,
`openings.unlock`, `openings.release` and
`notifications.send`, `notifications.announce` and `notifications.route`.

Garage open/close, door lock/unlock and door release require explicit confirmation.
Blade actions require no confirmation and qualify successful command dispatch without
claiming blade position. All three
notification actions require no confirmation, require a non-empty message and are
non-idempotent.

`wnhf.execution_manager` and `wnhf.execution_action` are diagnostic services; they
do not dispatch actions themselves.
