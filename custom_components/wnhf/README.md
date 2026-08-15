# Red Queen 1.0.0-rc3

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
- Version: `1.0.0-rc3`
- Channel: `release_candidate`
- Phase: `rc`
- Candidate: `rc3`
- Candidate development baseline: WNHF `1.29.1` / `WP-4.7.10.2`

## Stable 1.0 RC scope

Canonical mutating execution currently includes `lighting.turn_on`,
`lighting.turn_off`, `covers.open`, and `covers.close`.

Directional cover execution targets exactly one semantic cover and is guarded by
objective PLC end-state and movement feedback. Repeating a request when the requested
end state is already reached produces no command; repeating it while the cover is
already moving in the requested direction also produces no duplicate command.
Automatic direction reversal while the opposite movement is active remains blocked.

The cover Registry can additionally bind a `closed_percent_entity_id`. This PLC
feedback uses 0%=fully open and 100%=fully closed. Red Queen exposes it through the
native Home Assistant cover entity as `current_cover_position` after converting to
Home Assistant's 0=closed / 100=open convention.

Position feedback is read-only in RC3. `SET_POSITION` is not advertised because no
position target command exists. Blade/slat controls remain native-only because no
objective blade-position feedback is available.

See `docs/FEATURE_MATRIX.md` and `docs/RELEASE_NOTES_1.0.0-rc3.md`.

## Qualification

Canonical execution evidence is persisted per installation at
`/config/wnhf/qualification/execution_evidence_store.json`. Qualification is evidence,
not authorization, and never bypasses provider health, request validation, guards or
hardware feedback.
