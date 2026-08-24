# RC12 Dashboard Adapter & Lifecycle

Work package: **WP-4.7.18.4**

## Purpose

This work package introduces the only Home Assistant-specific persistence and
runtime-registration boundary for the generated Red Queen dashboard.

The prior layers remain pure:

1. `dashboard_model.py` compiles the semantic house.
2. `dashboard_binding.py` resolves current native Red Queen entity IDs.
3. `dashboard_renderer.py` produces a plain Lovelace configuration.
4. `dashboard_adapter.py` is the only layer that attaches and persists it.

## Ownership model

The dashboard is owned by Red Queen only after the Red Queen dashboard manifest
exists and contains the expected owner marker and adapter contract version.

Red Queen never adopts an existing panel or dashboard at the requested URL path.
If `red-queen` is already occupied by another panel/dashboard, creation fails
instead of overwriting it.

Default identity:

- dashboard id: `red-queen`
- URL path: `red-queen`
- title: `Red Queen`
- icon: `mdi:chess-queen`

## Home Assistant persistence boundary

RC12 does **not** edit `.storage` files.

The generated Lovelace config is persisted through Home Assistant's
`LovelaceStorage.async_save()` implementation.  Red Queen ownership metadata is
persisted through Home Assistant's `Store` helper.

The dashboard is intentionally not written through a newly-created
`DashboardsCollection`.  Home Assistant currently creates its live dashboard
collection inside Lovelace setup and does not expose that collection through
`hass.data`.  Creating a second collection against the same storage would leave
the live settings/WebSocket collection stale.

Instead Red Queen behaves as an integration-owned Lovelace panel:

- registers a `lovelace` built-in panel through the frontend API;
- installs its `LovelaceStorage` object into Lovelace runtime dashboard data;
- persists the dashboard config with the HA storage abstraction;
- removes only its runtime registration on integration unload.

This implementation detail is isolated inside `dashboard_adapter.py` so it can
be replaced if Home Assistant exposes a dedicated integration-facing dashboard
API later.

## Explicit write lifecycle

Creating/updating the dashboard is always explicit.

`async_apply(rendered)`:

- creates the managed dashboard when no ownership manifest exists;
- updates only the already-owned dashboard afterward;
- refuses URL/id ownership changes in RC12;
- saves the exact rendered config;
- stores render digest and renderer metadata;
- optionally stores a source registry digest.

Registry changes do not trigger `async_apply()` automatically.

## Startup lifecycle

Startup calls `async_restore()` only when a Red Queen dashboard manifest already
exists.

Restore:

- re-attaches the existing stored dashboard to Lovelace/frontend;
- does not rebuild the model;
- does not resolve bindings;
- does not render new YAML/config;
- does not overwrite the saved dashboard config.

This preserves the RC12 rule that dashboard regeneration is explicit.

## Unload lifecycle

Integration unload removes only the runtime dashboard mapping and frontend
panel.  It intentionally leaves:

- the Lovelace config storage;
- the Red Queen dashboard ownership manifest.

A subsequent integration load can therefore restore the same generated
dashboard without regenerating it.

## Status states

The adapter exposes deterministic lifecycle states:

- `not_created`
- `ready`
- `outdated`
- `detached`
- `recovery_mode`

When an expected render is supplied, its `config_sha256` is compared with the
stored manifest digest.  This is the basis for the later Configurator text
"Dashboard aktuell" / "Dashboard aktualisieren".

## Safety properties

- no direct `.storage` file writes;
- no adoption of foreign dashboards;
- no automatic regeneration during startup;
- no registry mutation;
- no provider/PLC binding;
- no safety/execution logic duplicated in the dashboard adapter;
- no dashboard data deletion on normal integration unload;
- Home Assistant recovery mode blocks dashboard writes.

## Next work package

WP-4.7.18.5 will compose model + floor metadata + entity bindings + renderer +
adapter into one dashboard generation service suitable for the Configurator.
