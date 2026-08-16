# Known Limitations and Deliberate RC5 Boundaries

## Canonical execution remains intentionally bounded

The canonical real-execution surface contains lighting on/off, directional cover
open/close, confirmed garage open/close, and confirmed door lock/unlock. Other
semantic/read capabilities do not automatically imply productive actuation.

## Covers

Cover open/close is canonical. Automatic reversal while movement in the opposite
direction is active remains blocked. Position feedback may be exposed read-only, but
canonical set-position and blade-position execution remain disabled because no
objective command/feedback contract is qualified for them.

## Garage

Canonical garage execution supports only `garage.open` and `garage.close`, both with
explicit confirmation and only from a proven opposite end position. Moving,
intermediate, unavailable, or contradictory states reject without an OSC pulse.
Canonical garage stop/toggle is intentionally not exposed because a residential OSC
pulse is stateful and can start movement when the actual motor state is not provable.

## Door opener

Electric door-opener commands remain outside canonical real execution. Existing
Access-level functionality is legacy/development surface only.

## Climate / temperature

Climate and temperature semantics remain planned future feature work.

## Media and notifications

Media and semantic notification/announcement domains remain planned future work.
