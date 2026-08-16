# WNHF Canonical Execution Manager API v1.1

The Execution Manager separates four concepts: declared, semantically ready, real
execution enabled, and executable now.

Current RC5 baseline: thirteen semantic actions are declared. Eight actions are
enabled through `wnhf.execution_execute`: `lighting.turn_on`, `lighting.turn_off`,
`covers.open`, `covers.close`, `garage.open`, `garage.close`, `openings.lock`, and
`openings.unlock`.

Garage open/close and door lock/unlock require explicit confirmation before provider
preflight can become executable.

`wnhf.execution_manager` and `wnhf.execution_action` are diagnostic services; they do
not dispatch hardware themselves.
