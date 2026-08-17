# WNHF Canonical Real Execution Contract

The stable real-execution entry is `wnhf.execution_execute`. RC6 enables nine
semantic actions: `lighting.turn_on`, `lighting.turn_off`, `covers.open`,
`covers.close`, `garage.open`, `garage.close`, `openings.lock`,
`openings.unlock` and `notifications.send`. Each targets one semantic object
through `target.object_id`.

Every real execution first passes dry-run validation and provider preflight. Only a
promoted validation plan can reach the Semantic Execution Router.

Lighting, covers, garage and locks preserve their existing feedback-aware safety and
idempotency contracts. Notification send instead requires a non-empty message, needs
no confirmation and is deliberately non-idempotent. Successful notification
execution proves completion of the Home Assistant dispatch call only. It records
framework verification at dispatch scope and does not claim hardware, delivery or
read verification.

`wnhf.execution_execute` performs a real action and supports response data
optionally. The legacy Decision-ID service `wnhf.execute` remains separate.
