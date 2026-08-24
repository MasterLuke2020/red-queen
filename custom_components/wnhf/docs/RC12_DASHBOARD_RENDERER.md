# RC12 Dashboard Renderer Core

Work package: **WP-4.7.18.3**

## Purpose

`dashboard_renderer.py` is the pure rendering layer between the RC12 semantic
Dashboard Model / Entity Binding and Home Assistant Lovelace storage.

```text
House
  -> DashboardModel
  -> DashboardBindings
  -> DashboardRenderer
  -> plain Lovelace config dict
  -> (later) Home Assistant dashboard storage adapter
```

The renderer performs **no storage mutation** and imports no Home Assistant
storage/dashboard internals.  This is intentional: the generated structure can
be inspected, serialized, hashed and tested before RC12 writes anything to a
Home Assistant installation.

## Native-only frontend contract

The renderer emits only native Home Assistant dashboard constructs:

- Sections views;
- grid sections;
- Heading cards;
- Tile cards;
- Button cards;
- Markdown cards;
- native navigation actions;
- native service/action calls;
- native `cover-open-close` Tile feature.

There is no dependency on Mushroom, button-card, stack-in-card, card-mod or any
other HACS/frontend custom card.

## Generated views

The first renderer core produces:

1. `overview`
   - house status;
   - openings;
   - lighting;
   - cover summary;
   - garage when present;
   - Plant Care summary when present;
   - security;
   - Red Queen health;
   - main actions;
   - floor navigation;
   - navigation to Plant Care and System.

2. one normal view per semantic floor;
   - native room status Markdown cards;
   - each room links to its stable room subview.

3. one `subview: true` view per enabled semantic room;
   - Light;
   - Openings;
   - Access;
   - Covers;
   - Plants;
   - absent categories are omitted.

4. optional `plants` view when Plant Care objects exist.

5. `system` diagnostics view.

## Binding behavior

The renderer never scans Home Assistant runtime states to discover which entity
belongs to a Red Queen object.  It uses only the previously resolved
`DashboardBindings`.

If an expected native entity cannot be resolved, the configured object remains
visible through a native Markdown diagnostic card.  This prevents silent loss
of configured house objects while avoiding invalid Lovelace entity references.

An entity that *is* registered but currently has state `unavailable` remains a
normal bound Tile card, satisfying the RC12 requirement that runtime
unavailability must not make configured objects disappear.

## Safety

Dashboard controls call native Red Queen entities/services only.  They do not
reimplement execution guards.

Examples:

- lights use the native `light.*` entity;
- covers use the native `cover.*` entity;
- door locks use native `lock.lock` / `lock.unlock` on the Red Queen lock;
- door release presses the native Red Queen release button;
- blade actions press the native Red Queen blade buttons;
- garage uses the native guarded garage cover;
- Plant Care presses the native Red Queen watering-history button.

The canonical Red Queen execution layer therefore remains the safety authority.

## Idempotency

`render_dashboard()` contains no timestamp or random ID in the generated config.
For identical `DashboardModel` and `DashboardBindings`, it produces the same
logical Lovelace configuration.

`DashboardRenderMetadata.config_sha256` is computed from canonical JSON and can
later be used by the dashboard lifecycle manager to detect whether a refresh
actually changes the generated dashboard.

## Scope boundary

WP-4.7.18.3 does **not**:

- create a Home Assistant dashboard;
- modify `.storage`;
- register a Lovelace resource;
- create helpers;
- write registry files;
- add weather/climate/media/energy content;
- introduce custom frontend cards.

The next work package can now focus on the Home Assistant dashboard adapter and
Configurator lifecycle while keeping this renderer stable and independently
testable.
