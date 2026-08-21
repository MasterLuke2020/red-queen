# Red Queen 1.0.0-rc10

Red Queen is a semantic home framework for Home Assistant. It models the house as
objects and state, evaluates context/rules/policies/decisions, resolves capabilities
and providers, and executes supported actions through explicit contracts and
feedback-aware guards.

## Technical identity

The public product name is **Red Queen**. The historical development name and the
Home Assistant technical integration domain remain **WNHF / `wnhf`** for
compatibility. Existing service IDs, config paths, unique IDs and persisted
qualification evidence are preserved throughout the 1.0 release line.

Canonical execution entry point: `wnhf.execution_execute`. The Decision-ID service
`wnhf.execute` remains a legacy compatibility path and is not recommended for new
automations.

## Release status

- Product: Red Queen
- Version: `1.0.0-rc10`
- Channel: `release_candidate`
- Phase: `rc`
- Candidate: `rc10`
- Candidate development baseline: WNHF `1.36.0` / `WP-4.7.16.0`
- Status: LIVE VERIFIED

## Stable 1.0 RC scope

Canonical mutating execution currently includes `lighting.turn_on`,
`lighting.turn_off`, `covers.open`, `covers.close`, `covers.blades_open`,
`covers.blades_close`, `garage.open`, `garage.close`, `openings.lock`,
`openings.unlock`, `openings.release` and
`notifications.send`, `notifications.announce`, `notifications.route` and
`plants.record_watering`.

`notifications.send` targets one provider-neutral semantic notification target. It
requires a non-empty `message`, accepts an optional string/null `title`, needs no
confirmation and is non-idempotent. Successful execution proves Home Assistant
dispatch only; delivery/read and hardware verification are not claimed. Qualification
evidence never persists message/title text.

`notifications.announce` natively owns TTS playback, urgency profiles and optional
Sonos-native announce overlays without a Home Assistant helper script. `notifications.route`
owns priority/profile channel selection for log, dashboard, mobile and voice outputs.
Installation-specific TTS and speaker entity IDs remain in the optional semantic
notification registry, never in the public action request.

Garage open/close targets exactly one semantic `garage_door` opening object. Both
actions require `confirmed: true`. The residential OSC pulse is dispatched only from
a proven opposite stable end state; moving, intermediate, unavailable or contradictory
states reject without a pulse.

Door lock/unlock requires explicit confirmation, a healthy motor-lock command,
objective lock feedback and a closed door contact. Directional cover execution is
guarded by objective end-state and movement feedback; automatic reversal remains
blocked.

Blade actions are non-idempotent and dispatch-scoped because objective blade-position
feedback is not required. Door release requires explicit confirmation, a closed-door
contact and an available configured command; successful execution does not claim
latch release or subsequent physical opening.

Plant Care loads an optional `plants.yaml` registry, exposes dashboard-ready status
sensors plus native record-watering buttons and atomically persists manual watering
history. Each plant entity pair belongs to its configured Red Queen room device;
button presses use the canonical execution service. A new plant remains
`unknown` until `plants.record_watering` records a real event. State-scoped success
does not claim independently observed physical watering or soil moisture.

RC10 adds a native room surface for every enabled opening, configured motor locks,
electric door releases, the garage door and explicit blade controls. Native lights,
covers, blades, access controls and Plant Care buttons all call the canonical
execution service; they do not bypass semantic guards or qualification.

See `docs/FEATURE_MATRIX.md` and `docs/RELEASE_NOTES_1.0.0-rc10.md`.

## Qualification

Canonical execution evidence is persisted per installation at
`/config/wnhf/qualification/execution_evidence_store.json`. Qualification is
evidence, not authorization, and never bypasses provider health, request validation,
guards or hardware/dispatch verification semantics.
