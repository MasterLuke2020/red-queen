# RC12 Native Entity Binding Contract

## Purpose

The generated Red Queen dashboard must bind semantic Red Queen objects to the
native Home Assistant entities that currently represent them.  Home Assistant
users are free to rename entity IDs, so the generator must never derive an
entity ID from a display name or assume that the original suggested entity ID
still exists.

RC12 resolves entities through the Home Assistant Entity Registry using:

1. the expected entity domain;
2. the Red Queen integration platform (`wnhf`);
3. the stable Red Queen native entity `unique_id`.

The resulting current `entity_id` is then used by the Lovelace renderer.

## Binding pipeline

```text
semantic object ID
        |
        v
stable Red Queen native unique_id
        |
        v
Home Assistant Entity Registry
        |
        v
current entity_id
        |
        v
generated dashboard
```

No runtime `states` scan is used and no provider entity is eligible for a
binding.

## RC11 native unique-id contracts pinned by RC12

| Semantic object | Native domain | Native unique_id |
| --- | --- | --- |
| light | `light` | `wnhf_<light object suffix>` |
| venetian blind | `cover` | `wnhf_<cover object suffix>` |
| cover position | `sensor` | `wnhf_cover_position_<cover suffix>` |
| blades open | `button` | `wnhf_blades_open_<cover suffix>` |
| blades close | `button` | `wnhf_blades_close_<cover suffix>` |
| opening state | `binary_sensor` | `wnhf_opening_<opening suffix>` |
| garage control | `cover` | `wnhf_garage_<opening suffix>` |
| door lock | `lock` | `wnhf_lock_<opening suffix>` |
| door release | `button` | `wnhf_door_release_<opening suffix>` |
| plant care | `sensor` | `wnhf_plant_care_<plant suffix>` |
| record watering | `button` | `wnhf_plant_water_<plant suffix>` |

Dots in the semantic suffix are replaced with underscores exactly as in RC11.

## Capability-aware expected entities

The binding layer expects optional native entities only when the semantic model
says the feature exists.

Examples:

- no cover position feedback -> no position sensor is expected;
- no blade commands -> no blade buttons are expected;
- no door lock -> no native lock is expected;
- no electric door opener -> no release button is expected;
- no garage STOP command does not remove the garage cover; STOP availability is
  handled by the native garage entity itself.

A configured capability whose native entity cannot be found is returned as a
binding issue.  The renderer must not silently substitute a provider entity.

## Renamed Home Assistant entity IDs

Because resolution uses `unique_id`, this remains valid:

```text
Red Queen semantic ID: light.eg.office.main
Native unique_id:      wnhf_eg_office_main
Original entity_id:    light.wnhf_eg_office_main
User renamed entity:   light.buero_spots
```

The next dashboard refresh resolves `light.buero_spots` from the Entity Registry
without changing the semantic Red Queen object.

## Side-effect boundary

`resolve_dashboard_bindings()` is read-only.  It does not:

- create or rename Home Assistant entities;
- enable disabled entities;
- mutate the Red Queen registry;
- write Lovelace storage;
- inspect or bind PLC/OPC-UA/MQTT provider entities.

## Completeness

The returned `DashboardBindings` contains every expected entity reference and a
deterministic issue list.  `complete` is true only when all expected native
entities are registered.

This gives the later configurator and renderer a clear choice: either render a
fully resolved dashboard or report exactly which Red Queen native binding is
missing.
