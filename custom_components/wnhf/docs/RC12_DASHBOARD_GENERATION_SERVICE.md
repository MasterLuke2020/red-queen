# RC12 Dashboard Generation Service

Work package: **WP-4.7.18.5**

The generation service is the orchestration boundary between the four RC12
Dashboard Foundation contracts:

1. `dashboard_model.py` compiles the semantic `House` into `DashboardModel`.
2. `dashboard_binding.py` resolves native Red Queen entities through stable
   Home Assistant Entity Registry `unique_id` values.
3. `dashboard_renderer.py` renders a deterministic native Lovelace config.
4. `dashboard_adapter.py` owns Home Assistant persistence and runtime panel
   registration.

`dashboard_service.py` composes these layers. It contains no card rendering and
no Lovelace storage implementation of its own.

## Read-only preview and status

`async_preview()` performs a complete compilation without persistence. It:

- refuses generation while the Red Queen engine is in registry recovery mode;
- reads the currently loaded semantic `House`;
- enriches floor display names/order from Home Assistant's Floor Registry;
- builds the dashboard model;
- resolves current native Red Queen entity IDs;
- renders the Lovelace configuration;
- calculates a line-ending-normalized SHA-256 digest of the dashboard-relevant
  registry source files.

`async_status()` compares this expected render with the dashboard manifest via
the lifecycle adapter. Therefore an entity rename, registry change, floor-name
change, or renderer change can make the managed dashboard `outdated` without
silently rewriting it.

## Explicit apply only

`async_apply()` is the only generation-service operation that requests a
persistent dashboard change. It still does not write Home Assistant storage
itself; it passes the rendered configuration to `RedQueenDashboardAdapter`.

No dashboard is generated during integration startup. Startup only initializes
the orchestration facade after the lifecycle adapter has restored an already
owned dashboard panel.

## Floor metadata

Managed RC11 rooms store the semantic floor segment generated from the Home
Assistant floor name. Manual registries may use an actual Home Assistant floor
ID. The RC12 service accepts both forms when looking up Floor Registry display
metadata. Unknown/manual floor IDs remain valid and fall back to the
platform-independent dashboard model's deterministic display name.

Floor `level`, when available, is used as the dashboard floor ordering hint.

## Source digest

The source digest covers only registries that can currently affect the RC12
dashboard:

- `rooms.yaml`
- `lights.yaml`
- `covers.yaml`
- `openings.yaml`
- `plants.yaml`

CRLF is normalized to LF. This prevents Windows working-copy line endings from
changing the logical source revision.

## Runtime contract

The initialized facade is stored under:

`hass.data[DOMAIN]["dashboard_generation_service"]`

The Configurator work package can retrieve it with
`dashboard_generation_service(hass)` and expose explicit **Create dashboard** /
**Update dashboard** actions without duplicating any generation logic.
