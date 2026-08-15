# WNHF Canonical Real Execution Contract

The stable real-execution entry is `wnhf.execution_execute`. RC4 enables six semantic
actions: `lighting.turn_on`, `lighting.turn_off`, `covers.open`, `covers.close`,
`openings.lock`, and `openings.unlock`. Each targets one semantic object through
`target.object_id`; parameters must be empty.

Every real execution first passes dry-run validation and provider preflight. Only a
promoted validation plan can reach the Semantic Execution Router.

Lighting confirms the requested ON/OFF state. Cover execution sends one dedicated
directional command and confirms either movement in the requested direction or the
requested end state. Door lock/unlock requires explicit confirmation, a closed door
contact, stable lock feedback, and confirmation of the requested lock state after
command dispatch.

A request whose target state is already satisfied sends no command and returns the
canonical `EXE-101` path. Cover requests already moving in the requested direction
return `EXE-102`. Opposite cover movement and open-door lock-state changes are blocked
by provider preflight.

`wnhf.execution_execute` performs a real action and supports response data optionally.
The legacy Decision-ID service `wnhf.execute` remains separate.
