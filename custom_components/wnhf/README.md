# Red Queen 1.0.0-rc1

Red Queen is a semantic home framework for Home Assistant. It models the house as
objects and state, evaluates context/rules/policies/decisions, resolves capabilities
and providers, and executes supported actions through explicit contracts and
feedback-aware guards.

## Technical identity

The public product name is **Red Queen**. The historical development name and the
Home Assistant technical integration domain remain **WNHF / `wnhf`** for compatibility.
This is intentional: existing service IDs, config paths, unique IDs and persisted
qualification evidence are not renamed for the 1.0 release line.

Canonical execution entry point:

```text
wnhf.execution_execute
```

The older Decision-ID service `wnhf.execute` remains a legacy compatibility path and
is not recommended for new automations.

## Release status

- Product: Red Queen
- Version: `1.0.0-rc1`
- Channel: `release_candidate`
- Phase: `rc`
- Candidate: `rc1`
- Verified development baseline: WNHF `1.27.0` / `WP-4.7.9.1`

## Stable 1.0 RC scope

The RC includes the semantic house/room model, lighting, openings, cover state,
security, providers, capabilities, qualification, validation, rules, context,
policies, decisions, canonical execution and scheduler diagnostics.

The stable canonical mutating execution surface is intentionally narrower than the
semantic model. At RC1, `lighting.turn_off` is the canonical real-execution action.
Cover state/snapshots are present, while canonical mutating cover actions are not yet
part of the stable execution surface. Climate, media, notifications and active garage
actuation remain planned domains.

See `docs/FEATURE_MATRIX.md` and `docs/RELEASE_NOTES_1.0.0-rc1.md`.

## Qualification

Canonical execution evidence is collected automatically and persisted per installation:

```text
/config/wnhf/qualification/execution_evidence_store.json
```

Qualification is evidence, not authorization. It never bypasses provider health,
request validation, confirmation policies, idempotency guards or hardware feedback.
