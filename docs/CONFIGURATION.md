# Configuration

Red Queen keeps its technical configuration namespace under `/config/wnhf` for compatibility.

## Registry root

```text
/config/wnhf/house/registry/
├── rooms.yaml
├── lights.yaml
├── covers.yaml
└── openings.yaml
```

All registry files use YAML dictionaries at the root and stable semantic object IDs.

## Rooms

`rooms.yaml` contains a `rooms:` list. Supported fields include:

- `id` — required stable string ID;
- `name` — required display name;
- `floor` — required floor ID;
- `numeric_id` — optional unique integer;
- `type` — optional, defaults to `room`;
- `enabled` — optional boolean, defaults to `true`;
- `tags` — optional string list;
- `aliases` — optional string list.

Example:

```yaml
rooms:
  - id: house.eg.kitchen
    name: Küche
    floor: eg
    type: room
    enabled: true
    tags: [living]
```

## Lights

`lights.yaml` contains a `lights:` list. A light requires `id`, `name` and a valid `room`. Supported `control_mode` values are `toggle`, `monitor_only` and `reserved`.

State feedback can be supplied through one `state.entity_id` and/or multiple `states` entries. A command can define `command.entity_id`.

Example matching the canonical RC1 execution model:

```yaml
lights:
  - id: light.eg.kitchen.spots
    name: Küche Spots
    room: house.eg.kitchen
    enabled: true
    control_mode: toggle
    command:
      entity_id: button.btwebeglichtkuechespots
    state:
      entity_id: binary_sensor.qxeglichtkuechespots
```

For an enabled `toggle` light, missing command or missing feedback is reported as a registry warning.

## Covers

`covers.yaml` contains a `covers:` list. RC1 supports the registry model for `type: venetian_blind`. The current loader requires command entity IDs for open/close/blades-open/blades-close and feedback entity IDs for open/closed/opening/closing, plus a non-empty `capabilities` list.

The semantic/read surface is part of RC1; canonical mutating cover execution is not.

## Openings

`openings.yaml` models `window`, `sliding_door`, `door` and `garage_door` objects. Ordinary openings use state feedback plus configured open-state values. Door objects may additionally define lock feedback/commands and an electric door opener. Garage doors may define two-sensor feedback plus toggle/optional stop commands.

Some Access execution services remain legacy/development surfaces in RC1. They are not the canonical new-automation route.

## Rules

Directory:

```text
/config/wnhf/contexts/rules/
```

All `*.yaml` and `*.yml` files are loaded. Missing directory is valid and yields an empty rule registry. Each file may contain `rule:` or `rules:`. A rule has an ID, at least one condition and a non-empty result map.

Supported operators:

`eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`, `contains`, `truthy`, `falsy`, `exists`, `not_exists`.

## Policies

Directory:

```text
/config/wnhf/policies/
```

`settings.yaml` may set the policy mode; current default is `monitor`. Other YAML files may contain `policy:` or `policies:`. Policy decisions are `allow` or `deny`. Missing policy configuration is valid.

## Decisions

Directory:

```text
/config/wnhf/decisions/
```

YAML files may contain `decision:` or `decisions:`. Definitions include stable ID, semantic action, target map, optional policy and context rules. The Decision-ID execution service is a legacy compatibility path; new productive automation should target the canonical semantic execution API instead.

## Persistence

Canonical qualification evidence is stored at:

```text
/config/wnhf/qualification/execution_evidence_store.json
```

Do not treat this file as configuration to hand-edit during normal operation.
