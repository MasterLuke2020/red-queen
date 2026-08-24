# RC12 Configurator Dashboard Menu

Work package: `WP-4.7.18.6`

## Purpose

Expose the RC12 generated-dashboard pipeline through the existing Red Queen
Options Flow without introducing automatic Lovelace writes.

The managed Configurator menu gains a `Dashboard` entry. Opening it is read-only:
Red Queen compiles the current registry, resolves native entity bindings, renders
the expected dashboard and compares that render with the persisted dashboard
manifest.

The menu then exposes exactly one explicit write action:

- `Dashboard erstellen` / `Create dashboard` when no Red Queen dashboard exists.
- `Dashboard aktualisieren` / `Update dashboard` once the dashboard is owned by
  Red Queen.

Selecting that menu action is the explicit mutation boundary. Only then does the
Options Flow call `RedQueenDashboardGenerationService.async_apply()`.

## Status shown to the user

The dashboard page exposes:

- lifecycle state (`not_created`, `ready`, `outdated`, `detached` or recovery),
- managed dashboard path,
- generated floor/room/object counts,
- resolved versus expected native Red Queen entity bindings,
- unresolved binding issue count.

No provider/PLC entity is selected or written by this flow.

## Refresh behavior

Registry mutations continue to use the existing OptionsFlowWithReload behavior.
Reloading Red Queen restores an already-owned dashboard panel but does not
regenerate its configuration. The next Dashboard status visit therefore reports
`Aktualisierung verfügbar` / `update available` whenever the generated render
differs from the persisted render digest.

## Error boundary

Generation or adapter errors abort the dashboard action with a localized
Configurator message. Existing registry files, existing user dashboards and the
last successfully persisted Red Queen dashboard remain untouched by the
Configurator flow itself.
