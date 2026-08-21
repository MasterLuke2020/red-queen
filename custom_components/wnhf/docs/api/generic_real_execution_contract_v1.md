# WNHF Canonical Real Execution Contract

The stable real-execution entry is `wnhf.execution_execute`. RC10 enables fifteen
semantic actions: `lighting.turn_on`, `lighting.turn_off`, `covers.open`,
`covers.close`, `covers.blades_open`, `covers.blades_close`, `garage.open`,
`garage.close`, `openings.lock`, `openings.unlock`, `openings.release`,
`notifications.send`, `notifications.announce` and
`notifications.route` and `plants.record_watering`. Each targets one semantic
object through `target.object_id`.

Every real execution first passes dry-run validation and provider preflight. Only a
promoted validation plan can reach the Semantic Execution Router.

Lighting, directional covers, garage and locks preserve their feedback-aware safety
and idempotency contracts. Blade actions are deliberately non-idempotent and prove
only dispatch because typical venetian blinds expose no blade-position feedback.
Door release requires explicit confirmation plus a closed door contact and proves
only dispatch; it does not claim latch release or subsequent physical opening.
Notification send requires a non-empty message, needs
no confirmation and is deliberately non-idempotent. Successful notification
execution proves completion of the Home Assistant dispatch call only. It records
framework verification at dispatch scope and does not claim hardware, delivery or
read verification. Native announcements prove acceptance of the configured TTS
dispatch only. For Sonos native announce, Sonos owns overlay restoration and Red
Queen does not claim audible playback or restoration completion. Native routing
records every selected channel result and fails visibly on partial channel failure.
Plant watering atomically appends one history event and verifies persistent state.
Its `state` scope is framework-verified but not hardware-verified and does not claim
physical watering or soil moisture.

`wnhf.execution_execute` performs a real action and supports response data
optionally. The legacy Decision-ID service `wnhf.execute` remains separate.
