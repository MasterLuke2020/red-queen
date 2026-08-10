# WNHF Canonical Real Execution Contract

The stable real-execution entry is `wnhf.execution_execute`. The current RC
surface enables exactly one semantic action: `lighting.turn_off`, targeting one
semantic light object through `target.object_id`. Parameters must be empty.

Every real execution first passes the same dry-run validation and provider
preflight. Only a promoted validation plan can reach the Semantic Execution Router.
The Lighting provider retains the existing feedback-guarded momentary pipeline:
no toggle pulse is sent when feedback already reports OFF, and a sent command is
considered successful only after required feedback confirmation.

The legacy Decision-ID service `wnhf.execute` is separate and is not recommended
for new automations.
