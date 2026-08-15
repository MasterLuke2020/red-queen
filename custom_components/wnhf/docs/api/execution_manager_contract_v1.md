# WNHF Canonical Execution Manager API v1.1

The Execution Manager separates four concepts: declared, semantically ready, real
execution enabled, and executable now.

Current RC4 baseline: ten semantic actions are declared. Six actions are enabled
through `wnhf.execution_execute`: `lighting.turn_on`, `lighting.turn_off`,
`covers.open`, `covers.close`, `openings.lock`, and `openings.unlock`.

`openings.lock` and `openings.unlock` require explicit confirmation before their
provider preflight can become executable.

`wnhf.execution_manager` and `wnhf.execution_action` are diagnostic services; they do
not dispatch hardware themselves.
