# WNHF Canonical Execution Manager API v1.1

The Execution Manager separates four concepts: declared, semantically ready, real
execution enabled, and executable now.

Current RC3 baseline: eight semantic actions are declared. Four actions are enabled
through `wnhf.execution_execute`: `lighting.turn_on`, `lighting.turn_off`,
`covers.open`, and `covers.close`.

`wnhf.execution_manager` and `wnhf.execution_action` are diagnostic services; they do
not dispatch hardware themselves.
