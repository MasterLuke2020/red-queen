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

Example matching the canonical execution model:

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

`covers.yaml` contains a `covers:` list. The current registry supports `type: venetian_blind`. The current loader requires command entity IDs for open/close/blades-open/blades-close and feedback entity IDs for open/closed/opening/closing, plus a non-empty `capabilities` list.

The semantic/read surface and canonical `covers.open` / `covers.close` execution are active; position and blade commands remain non-canonical.

## Openings

`openings.yaml` models `window`, `sliding_door`, `door` and `garage_door` objects. Ordinary openings use state feedback plus configured open-state values. Door objects may additionally define lock feedback/commands and an electric door opener. Garage doors may define two-sensor feedback plus toggle/optional stop commands.

Some Access execution services remain legacy/development surfaces. Canonical garage open/close and door lock/unlock should use `wnhf.execution_execute` for new automations.

## Notification targets

`notification_targets.yaml` is an optional provider-owned registry next to the
physical house registries:

```text
/config/wnhf/house/registry/notification_targets.yaml
```

Example:

```yaml
notification_targets:
  - id: notification.target.lukas
    name: Lukas
    enabled: true
    provider: home_assistant_notify_entity
    entity_id: notify.motorola_edge_40_neo
```

Target IDs must use the `notification.target.` prefix. RC6 supports the provider
value `home_assistant_notify_entity`; `entity_id` must reference a Home Assistant
`notify.*` entity. The registry is reloaded during provider preflight.

Canonical `notifications.send` requires one semantic target and a non-empty message:

```yaml
action: wnhf.execution_execute
data:
  action_id: notifications.send
  target:
    object_id: notification.target.lukas
  parameters:
    message: Red Queen Testnachricht
    title: Optionaler Titel
```

The action needs no confirmation and identical requests are separate sends.

The same optional file may define native TTS announcement targets and semantic
notification routes. No Home Assistant script or event automation is required.

```yaml
announcement_targets:
  - id: announcement.target.house
    name: Whole-house announcement
    enabled: true
    provider: home_assistant_tts_sonos
    tts_entity_id: tts.google_translate_de_at
    cache: false
    with_group: true
    levels:
      info:
        speakers: [media_player.office]
        volume: 0.35
        prefix: null
      notice:
        speakers: [media_player.office]
        volume: 0.35
        prefix: Hinweis.
      warning:
        speakers: [media_player.office]
        volume: 0.45
        prefix: Warnung.
      alarm:
        speakers: [media_player.office]
        volume: 0.55
        prefix: Achtung!

notification_routes:
  - id: notification.route.house
    name: House notification route
    enabled: true
    notification_target_ids: [notification.target.lukas]
    announcement_target_id: announcement.target.house
    log_enabled: true
    dashboard_enabled: true
    context:
      quiet_mode_entity_id: binary_sensor.quiet_mode
      house_state_entity_id: sensor.house_presence_state
      voice_blocked_states: [away, vacation, unknown, unavailable]
```

`provider: home_assistant_tts_sonos` uses `media_player.play_media` with a TTS
Media Source, `announce: true` and the level volume in `extra.volume`. Sonos owns
music ducking and restoration; Red Queen deliberately sends no second snapshot or
restore command. The retained `with_group` field is accepted for registry
compatibility but is not used by the native announce path. The portable
`home_assistant_tts` provider retains/restores speaker volume but cannot promise
vendor-specific playback restoration.

Direct announcement example:

```yaml
action: wnhf.execution_execute
data:
  action_id: notifications.announce
  target:
    object_id: announcement.target.house
  parameters:
    message: Die Garage ist noch geöffnet.
    level: warning
```

Native route example:

```yaml
action: wnhf.execution_execute
data:
  action_id: notifications.route
  target:
    object_id: notification.route.house
  parameters:
    message: Die Garage ist noch geöffnet.
    title: Garage
    priority: warning
    profile: standard
    source: garage_monitor
    category: security
```

Routing profiles preserve the original WNHF prototype semantics: `standard` uses
dashboard/mobile plus context-allowed voice; `silent` suppresses voice; `voice`
uses dashboard plus context-allowed voice; `mobile` selects mobile only;
`broadcast` selects every channel and deliberately bypasses the voice context guard.

The dashboard channel creates a persistent Home Assistant notification only for
`warning` and `critical`. Lower priorities remain visible in route diagnostics and
the log channel without creating a persistent dashboard message.

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
