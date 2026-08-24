# RC12 Dashboard Implementation Plan

## WP-4.7.18.1 — Dashboard Model & Generator Skeleton

Status: first implementation slice.

This slice adds only the platform-independent dashboard contract/model. It intentionally does **not** register, write, or render a Home Assistant dashboard yet.

### Deliverables

- `dashboard_model.py`
- `RC12_DASHBOARD_CONTRACT.md`
- deterministic floor and room grouping;
- deterministic stable paths;
- feature flags and object counts;
- room-level semantic specs for lights, covers, openings/access and plants;
- no Home Assistant storage mutation;
- no runtime behavior change to existing RC11 entities or execution.

### Important model decisions

- only enabled rooms are included;
- only controllable lights are included because RC11 creates native `light` entities only for controllable lights;
- all enabled covers are included;
- all enabled openings are included;
- all enabled plants are included;
- floor display metadata is injected later by the Home Assistant adapter, while `Room.floor_id` remains the stable semantic grouping key;
- native entity IDs are deliberately absent from the pure model.

## WP-4.7.18.2 — Native Entity Binding

Planned next:

- resolve Red Queen native entity IDs from Home Assistant's Entity Registry;
- bind semantic object IDs to native light/cover/opening/lock/button/sensor entities;
- resolve global Red Queen diagnostic/aggregate entities;
- re-resolve bindings on explicit dashboard refresh;
- never bind provider command/feedback entities into the generated dashboard.

## WP-4.7.18.3 — Lovelace Adapter & Persistence Boundary

Home Assistant 2026 uses storage-backed dashboard collections internally. Dashboard creation itself is not exposed as a stable public custom-integration API, so RC12 will isolate all Lovelace persistence behind one adapter module instead of letting dashboard code touch `.storage` or `hass.data` throughout the integration.

The adapter must:

- own one dedicated Red Queen dashboard URL path;
- refuse to overwrite a non-Red-Queen dashboard at that path;
- never alter the default Lovelace dashboard;
- save a fully rendered dashboard only after successful model/entity validation;
- record generator metadata/digest for idempotent refresh;
- fail safely if the Home Assistant dashboard API changes.

## WP-4.7.18.4+ — Rendering

After the persistence boundary is proven on the test system:

- overview renderer;
- floor renderer;
- room subview renderer;
- plants/system views;
- configurator create/refresh/status;
- translations;
- live qualification.
