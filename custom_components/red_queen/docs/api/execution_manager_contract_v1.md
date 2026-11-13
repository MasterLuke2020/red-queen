# WNHF Canonical Execution Manager API v1.1

The Execution Manager separates four concepts: declared, semantically ready, real
execution enabled and executable now.

Current RC11 candidate baseline: twenty-three semantic actions across eight capabilities
are declared. Sixteen actions are enabled through `wnhf.execution_execute`:
`lighting.turn_on`,
`lighting.turn_off`, `covers.open`, `covers.close`, `covers.blades_open`,
`covers.blades_close`, `garage.open`, `garage.close`, `garage.stop`, `openings.lock`,
`openings.unlock`, `openings.release` and
`notifications.send`, `notifications.announce`, `notifications.route` and
`plants.record_watering`.

Garage open/close/stop, door lock/unlock and door release require explicit confirmation. Garage STOP is real-execution-enabled only when the target configures a dedicated STOP command; runtime execution still requires observed motion.
Blade actions require no confirmation and qualify successful command dispatch without
claiming blade position. All three
notification actions require no confirmation, require a non-empty message and are
non-idempotent.
Plant watering requires no confirmation and qualifies only the verified persistent
state mutation, not an independently observed physical watering event.

`wnhf.execution_manager` and `wnhf.execution_action` are diagnostic services; they
do not dispatch actions themselves.
