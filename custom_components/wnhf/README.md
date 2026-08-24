# Red Queen 1.0.0-rc12

Red Queen is a semantic home framework for Home Assistant. The public product name is
**Red Queen**; the technical Home Assistant domain remains **`wnhf`** for compatibility.

## Release identity

- Product: Red Queen
- Version: `1.0.0-rc12`
- Channel: `release_candidate`
- Candidate: `rc12`
- Development baseline: WNHF `1.38.0` / `WP-4.7.18.0`
- Canonical execution entry: `wnhf.execution_execute`
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11` (unchanged in RC12)

## RC12 Generated Dashboard Foundation

RC12 adds a generated integration-owned dashboard at `/red-queen`.

The dashboard is built from the Red Queen semantic House model, resolves current
native entity IDs through stable unique IDs, and renders only native Home Assistant
cards. It includes overview, floor views, room subviews, Plant Care and
System/Diagnostics.

The managed configurator exposes explicit dashboard create/update actions. Existing
manual registries stay read-only for semantic configuration but can use the dashboard.
Dashboard refresh is deterministic and digest-based; Home Assistant restart restores
the saved dashboard without implicit regeneration.

The dashboard never dispatches provider entities directly. Lights, covers, blades,
`garage.stop`, door access actions and Plant Care use native Red Queen entities that
route through canonical execution and preserve all safety guards.

## Managed configurator

The managed configurator supports transaction-safe commissioning for rooms, impulse
lights, venetian blinds, windows, sliding doors, doors, garage doors and Plant Care.
Existing manual registries remain read-only and are never silently adopted.

## Qualification status

The dashboard implementation was live verified on a dedicated Home Assistant test
instance on 2026-08-24, including `168/168` native entity bindings, create/update,
room/floor/plant/system navigation and restart persistence. Exact final candidate
package qualification remains pending after release metadata/checksum finalization.

See `docs/FEATURE_MATRIX.md`, `docs/RC12_CANDIDATE_VALIDATION.md`, and
`docs/RELEASE_NOTES_1.0.0-rc12.md`.
