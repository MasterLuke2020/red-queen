# Red Queen 1.0.0-rc13

Red Queen is a semantic home framework for Home Assistant. The public product name is
**Red Queen**; the technical Home Assistant domain remains **`wnhf`** for compatibility.

## Release identity

- Product: Red Queen
- Version: `1.0.0-rc13`
- Channel: `release_candidate`
- Candidate: `rc13`
- Development baseline: WNHF `1.39.0` / `WP-4.7.19.0`
- Canonical execution entry: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11`

## RC13 managed configurator

The managed configurator supports transaction-safe commissioning and maintenance for
rooms, impulse lights, venetian blinds, windows, sliding doors, doors, garage doors
and Plant Care.

RC13 adds edit/update, enable/disable and guarded deletion. Semantic IDs remain stable.
Every mutation is ownership-gated, validated as a complete registry bundle and
protected by backup/atomic-replace/rollback. Referenced rooms and the last managed
room cannot be deleted. Manual registries remain read-only.

## Diagnostics and dashboard freshness

Entity/Provider diagnostics inspect only entity IDs explicitly configured in the Red
Queen registry and classify missing, HA-disabled, unavailable, unknown and
state-missing references.

The generated `/red-queen` dashboard resolves native Red Queen entities through stable
unique IDs and now tracks freshness against the semantic registry source SHA.
Dashboard create/update remains explicit and reload-safe. `garage.stop` and all other
physical controls continue through canonical guarded execution.

## Qualification status

RC13 managed maintenance, diagnostics, dashboard freshness and restart persistence
were live verified on 2026-09-17. The release is frozen for final exact-package
requalification before tag/publication.

See `docs/FEATURE_MATRIX.md`, `docs/RC13_CANDIDATE_VALIDATION.md`, and
`docs/RELEASE_NOTES_1.0.0-rc13.md`.
