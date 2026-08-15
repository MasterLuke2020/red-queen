# WNHF Canonical Real Execution Contract

The stable real-execution entry is `wnhf.execution_execute`. The RC2 candidate
surface enables two semantic lighting actions: `lighting.turn_on` and
`lighting.turn_off`, each targeting one semantic light object through
`target.object_id`. Parameters must be empty.

Every real execution first passes the same dry-run validation and provider
preflight. Only a promoted validation plan can reach the Semantic Execution Router.
The Lighting provider uses a feedback-guarded momentary pipeline for both target
states: no toggle pulse is sent when feedback already reports the requested state,
and a sent command is considered successful only after required feedback
confirmation.

`wnhf.execution_execute` performs a real action and supports response data
optionally. Callers that request a response receive the complete canonical execution
result; ordinary dashboard or automation calls may execute without requesting a
response.

The legacy Decision-ID service `wnhf.execute` is separate and is not recommended
for new automations.
