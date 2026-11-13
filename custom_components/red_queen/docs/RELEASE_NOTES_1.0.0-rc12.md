# Red Queen 1.0.0-rc12 Release Notes

## Generated Dashboard Foundation

RC12 adds a generated, integration-owned native Home Assistant dashboard at
`/red-queen`.

### Highlights

- Semantic dashboard model derived from the Red Queen House registry.
- Stable unique-ID based resolution to current Home Assistant entity IDs.
- Native Lovelace renderer with overview, floors, room subviews, Plant Care and
  System/Diagnostics.
- Explicit **Dashboard erstellen** and **Dashboard aktualisieren** lifecycle actions.
- Deterministic digest-based update detection.
- Restart persistence without automatic regeneration.
- Manual registries can use the dashboard while remaining read-only for semantic
  configuration.
- No mandatory HACS/custom frontend card dependency.
- No direct provider action binding; canonical Red Queen safety remains authoritative.
- Improved semantic unavailable-state presentation and floor labels.
- Reduced validator sensor attributes to avoid Recorder's 16-KB attribute warning.

### Compatibility

- Technical domain remains `wnhf`.
- Canonical execution service remains `wnhf.execution_execute`.
- Canonical API remains `1.0`.
- Canonical real-execution contract remains `2.3-rc11`; RC12 does not change physical
  execution semantics.
- Existing RC11 managed/manual registry ownership rules remain compatible.

### Live validation before exact package finalization

On 2026-08-24 the dashboard implementation passed dedicated Home Assistant live
validation with 3 floors, 23 rooms and 168/168 expected native entity bindings. Create,
update, navigation and restart persistence passed. Exact final candidate package
qualification is still required after metadata/checksum finalization.
