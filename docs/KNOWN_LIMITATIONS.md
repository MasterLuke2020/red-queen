# Known Limitations and Deliberate RC7 Candidate Boundaries

## Canonical execution remains intentionally bounded

The canonical real-execution surface contains lighting on/off, directional cover
open/close, confirmed garage open/close, confirmed door lock/unlock, semantic
notification dispatch, native announcements and notification routing. Other
semantic/read capabilities do not automatically imply productive actuation.

## Notifications

RC7 retains `notifications.send` and adds native `notifications.announce` and
`notifications.route`. Installation-specific targets require explicit registry
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
