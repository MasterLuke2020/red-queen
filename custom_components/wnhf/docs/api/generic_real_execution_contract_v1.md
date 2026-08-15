# WNHF Canonical Real Execution Contract

The stable real-execution entry is `wnhf.execution_execute`. RC3 enables four semantic
actions: `lighting.turn_on`, `lighting.turn_off`, `covers.open`, and `covers.close`.
Each targets one semantic object through `target.object_id`; parameters must be empty.

Every real execution first passes dry-run validation and provider preflight. Only a
promoted validation plan can reach the Semantic Execution Router.

Lighting confirms the requested ON/OFF state. Cover execution sends one dedicated
directional command and confirms either movement in the requested direction or the
requested end state. A second request while the requested movement is already in
progress returns `EXE-102` without sending a duplicate command. A request while the
opposite movement is active is rejected rather than automatically reversing direction.

Continuous cover position is supplemental read-only feedback and is not a canonical
command parameter. Blade/slat commands are not canonical because blade-position
feedback is unavailable.

`wnhf.execution_execute` performs a real action and supports response data optionally.
The legacy Decision-ID service `wnhf.execute` remains separate.
