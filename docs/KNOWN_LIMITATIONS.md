# Known Limitations and Deliberate RC6 Boundaries

## Canonical execution remains intentionally bounded

The canonical real-execution surface contains lighting on/off, directional cover
open/close, confirmed garage open/close, confirmed door lock/unlock and semantic
notification dispatch. Other semantic/read capabilities do not automatically imply
productive actuation.

## Notifications

RC6 supports `notifications.send` with a required non-empty `message` and optional
`title`. It does not yet support announcements/TTS, priority or category routing,
presence-based routing, multiple recipients in one target, or arbitrary
provider-specific data.

A successful result proves that Home Assistant accepted the notify service call. It
does not prove handset delivery or a read receipt. Qualification is therefore
framework-verified at dispatch scope and not hardware-verified.

## Covers

Cover open/close is canonical. Automatic reversal while movement in the opposite
direction is active remains blocked. Position feedback may be exposed read-only, but
canonical set-position and blade-position execution remain disabled because no
objective command/feedback contract is qualified for them.

## Garage

Canonical garage execution supports only `garage.open` and `garage.close`, both with
explicit confirmation and only from a proven opposite end position. Moving,
intermediate, unavailable or contradictory states reject without an OSC pulse.
Canonical garage stop/toggle is intentionally not exposed.

## Door opener

Electric door-opener commands remain outside canonical real execution. Existing
Access-level functionality is a legacy/development surface only.

## Climate / temperature and media

Climate/temperature semantics and media semantics remain planned future work.
