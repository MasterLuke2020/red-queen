# Red Queen 1.0.0-rc5

Red Queen is a semantic home framework for Home Assistant. It models the house as
objects and state, evaluates context/rules/policies/decisions, resolves capabilities
and providers, and executes supported actions through explicit contracts and
feedback-aware guards.

## Technical identity

The public product name is **Red Queen**. The historical development name and the
Home Assistant technical integration domain remain **WNHF / `wnhf`** for compatibility.
Existing service IDs, config paths, unique IDs and persisted qualification evidence
are preserved throughout the 1.0 release line.

Canonical execution entry point: `wnhf.execution_execute`. The Decision-ID service
`wnhf.execute` remains a legacy compatibility path and is not recommended for new
automations.

## Release status

- Product: Red Queen
- Version: `1.0.0-rc5`
- Channel: `release_candidate`
- Phase: `rc`
- Candidate: `rc5`
- Candidate development baseline: WNHF `1.31.0` / `WP-4.7.12.1`

## Stable 1.0 RC scope

Canonical mutating execution currently includes `lighting.turn_on`,
`lighting.turn_off`, `covers.open`, `covers.close`, `garage.open`, `garage.close`,
`openings.lock`, and `openings.unlock`.

Garage open/close targets exactly one semantic `garage_door` opening object. Both
actions require `confirmed: true`. The residential OSC pulse is dispatched only when
objective end-position feedback proves the door is at the opposite stable end state.
Already-satisfied requests send no pulse; moving, intermediate, unavailable, or
contradictory states are rejected. After dispatch, movement start and the requested
terminal end position are observed. Canonical `garage.stop` and `garage.toggle` are
intentionally not exposed.

Door lock/unlock targets exactly one semantic opening object. Both actions require
`confirmed: true`, require a healthy motor-lock command plus objective lock feedback,
and are blocked while the door contact reports open. Repeating an already-satisfied
lock state sends no command.

Directional cover execution targets exactly one semantic cover and is guarded by
objective PLC end-state and movement feedback. Repeating a request when the requested
end state is already reached produces no command; repeating it while the cover is
already moving in the requested direction also produces no duplicate command.
Automatic direction reversal while the opposite movement is active remains blocked.

See `docs/FEATURE_MATRIX.md` and `docs/RC5_CANDIDATE_VALIDATION.md`.

## Qualification

Canonical execution evidence is persisted per installation at
`/config/wnhf/qualification/execution_evidence_store.json`. Qualification is evidence,
not authorization, and never bypasses provider health, request validation, guards or
hardware feedback.
