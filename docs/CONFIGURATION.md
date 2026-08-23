# Configuration

Red Queen keeps its installation namespace under `/config/wnhf` for compatibility.

## Registry ownership modes

RC11 distinguishes three registry states:

- `uninitialized` — no usable Red Queen house registry exists yet;
- `manual` — registry files exist but are not owned by the RC11 configurator;
- `managed` — the configurator created the registry bundle and owns it through its
  management manifest.

**Manual registries remain read-only.** RC11 never silently adopts or rewrites an
existing manual registry.

The registry root is:

```text
/config/wnhf/house/registry/
├── rooms.yaml
├── lights.yaml
├── covers.yaml
├── openings.yaml
└── plants.yaml
```

Managed configuration backups are stored below:

```text
/config/wnhf/house/configuration_backups/
```

## Fresh commissioning

On an uninitialized installation, open **Settings → Devices & services → Red Queen →
Configure**.

The base flow can use Home Assistant Areas/Floors to create the initial managed room
registry. Empty managed registries for lights, covers, openings and plants are
created at the same time.

Semantic IDs for normal configurator-created objects are generated automatically.
Users select Home Assistant entities and provide user-facing names rather than
manually constructing Red Queen IDs.

## Managed configuration menu

RC11 supports guided creation of:

- rooms;
- impulse-controlled lights;
- venetian blinds;
- windows;
- sliding doors;
- doors with optional motor lock and/or electric release;
- garage doors;
- Plant Care objects.

Duplicate room/object combinations are rejected before a managed write.

Every managed mutation is rendered as a complete draft bundle and validated through
the production registry loader before replacement. Managed writes are staged,
backed up and rolled back if replacement fails.

`wnhf.configuration_snapshot` exposes mode, registry path, ownership manifest,
managed files, hashes, counts and validation state.

## Rooms

Rooms are selected from Home Assistant Areas, with optional Home Assistant Floor
context. The semantic room ID is generated automatically.

## Impulse lights

A managed impulse light uses:

- one `button.*` command entity;
- one `binary_sensor.*` objective feedback entity.

Native Red Queen light entities route through canonical `lighting.turn_on` /
`lighting.turn_off` execution and use feedback-aware no-action behavior when the
requested state is already satisfied.

## Venetian blinds

A managed venetian blind uses separate `button.*` open/close commands and objective
`binary_sensor.*` feedback for:

- open;
- closed;
- opening;
- closing.

Optional features:

- a read-only `sensor.*` closed-percent source (`0 = open`, `100 = closed`);
- separate blade-open and blade-close `button.*` commands.

Red Queen exposes Home Assistant current position from objective read-only feedback,
but deliberately does not advertise arbitrary `SET_POSITION`. Blade commands remain
separate buttons and are unavailable while the blind is moving.

## Openings

Supported opening types are:

- window;
- sliding door;
- door;
- garage door.

Windows and sliding doors use objective open/closed feedback.

A door can additionally configure:

- objective motor-lock feedback;
- separate lock and unlock pulse buttons;
- optional electric door-release pulse.

Lock/unlock and electric release remain blocked while the door is objectively open.

A garage door configures objective open and closed feedback plus its travel command.
A dedicated STOP command is optional. Canonical `garage.stop` is accepted only while
motion is objectively observed. STOP proves command dispatch only and does not infer
the resulting physical position.

## Plant Care

A managed plant stores:

- name;
- species;
- Red Queen room;
- optional location;
- watering interval in days;
- optional `sensor.*` moisture reference.

Watering history remains event/interval based. The optional moisture sensor is stored
as objective input metadata but does not alter the RC11 care state.

Each enabled plant exposes a room-associated Plant Care sensor and a native
**Gießen protokollieren / Record watering** button. The button invokes canonical
`plants.record_watering`; it records a completed real watering event and does not
control irrigation.

Persistent watering history is stored at:

```text
/config/wnhf/plant_care/watering_history.json
```

## Notification targets

`notification_targets.yaml` remains an optional provider-owned registry next to the
physical house registries. Existing semantic direct notification, TTS announcement
and notification-route contracts are unchanged by RC11.

Canonical entry points remain:

- `notifications.send`
- `notifications.announce`
- `notifications.route`

Raw Home Assistant notify/TTS/media-player IDs remain installation configuration and
are not accepted as provider-neutral semantic request targets.

## Rules, policies and decisions

Rules remain under `/config/wnhf/contexts/rules/`, policies under
`/config/wnhf/policies/`, and decision definitions under `/config/wnhf/decisions/`.

`wnhf.execution_execute` is the canonical productive execution entry point.
Decision-ID execution through `wnhf.execute` remains a legacy compatibility path.

## Qualification persistence

Canonical execution evidence is stored at:

```text
/config/wnhf/qualification/execution_evidence_store.json
```

Qualification evidence is not configuration and should not be hand-edited during
normal operation.
