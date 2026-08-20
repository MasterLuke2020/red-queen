# Red Queen 1.0.0-rc7

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
- Version: `1.0.0-rc7`
- Channel: `release_candidate`
- Phase: `rc`
- Candidate: `rc7`
- Candidate development baseline: WNHF `1.33.0` / `WP-4.7.13.2`
- Status: LIVE VERIFIED on 2026-08-20; release preparation ready

## Stable 1.0 RC scope

Canonical mutating execution currently includes `lighting.turn_on`,
`lighting.turn_off`, `covers.open`, `covers.close`, `garage.open`,
`garage.close`, `openings.lock`, `openings.unlock` and
`notifications.send`, `notifications.announce` and `notifications.route`.

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

See `docs/FEATURE_MATRIX.md` and `docs/RELEASE_NOTES_1.0.0-rc7.md`.

## Qualification

Canonical execution evidence is persisted per installation at
`/config/wnhf/qualification/execution_evidence_store.json`. Qualification is
evidence, not authorization, and never bypasses provider health, request validation,
guards or hardware/dispatch verification semantics.
