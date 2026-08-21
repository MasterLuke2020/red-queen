# Known Limitations and Deliberate RC9 Candidate Boundaries

## Canonical execution remains intentionally bounded

The canonical real-execution surface contains lighting on/off, directional cover
open/close, confirmed garage open/close, confirmed door lock/unlock, semantic
blade open/close, confirmed electric door release, notification dispatch, native
announcements and notification routing. Other
semantic/read capabilities do not automatically imply productive actuation.

## Plant Care

RC9 uses configured care intervals and persistent manual watering history. It does
not infer an initial watering time, evaluate soil moisture, adjust intervals for
season/light/climate, or automatically dispatch reminders. A successful
`plants.record_watering` result proves the persistent state event only; it does not
prove that a person physically watered the plant.
The per-plant button is deliberately non-idempotent: every successful press appends
one history event. Red Queen cannot distinguish an intentional second watering from
an accidental second press, so dashboard confirmation is recommended.

## Notifications

RC9 inherits the live-verified `notifications.send`, `notifications.announce` and
`notifications.route` contracts. Installation-specific targets require explicit registry
configuration; Red Queen deliberately does not auto-select speakers or recipients.
Context-aware voice routing currently consumes optional configured Home Assistant
quiet-mode and house-state entities. A first-class resident/presence model remains
future work.

A successful result proves that Home Assistant accepted the notify service call. It
does not prove handset delivery or a read receipt. Likewise, successful TTS dispatch
does not prove that a speaker was audible or a resident heard the message.
Qualification is framework-verified at dispatch scope and not hardware-verified.

Generic TTS targets can restore volume but cannot promise vendor-specific playback
or grouping restoration. `home_assistant_tts_sonos` uses the Home Assistant
media-player Sonos `announce` overlay. Sonos owns ducking and restoration; Red Queen
qualifies only dispatch and does not claim that restoration has completed.

## Covers

Cover open/close and blade open/close are canonical. Automatic reversal while
movement in the opposite direction is active remains blocked, and blade commands are
blocked while the cover is moving. Position feedback may be exposed read-only, but
canonical set-position execution remains disabled. Blade actions prove dispatch only;
they do not claim an objective blade angle or final blade state.

## Garage

Canonical garage execution supports only `garage.open` and `garage.close`, both with
explicit confirmation and only from a proven opposite end position. Moving,
intermediate, unavailable or contradictory states reject without an OSC pulse.
Canonical garage stop/toggle is intentionally not exposed.

## Door opener

`openings.release` is canonical and requires explicit confirmation, a configured
available command entity and a proven closed door contact. Success proves only that
Home Assistant completed the configured command dispatch; latch release and physical
door opening are not claimed.

## Climate / temperature and media

Climate/temperature semantics and media semantics remain planned future work.
