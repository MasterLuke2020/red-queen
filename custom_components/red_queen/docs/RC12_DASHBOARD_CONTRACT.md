# RC12 Dashboard Contract v1

## Release target

- Product: Red Queen `1.0.0-rc12`
- Work package: `WP-4.7.18.0 — Generated Dashboard Foundation`
- Dashboard contract: `1.0`

## Goal

A newly commissioned Red Queen installation can create a useful Home Assistant dashboard from the Red Queen semantic house model without manual dashboard YAML.

The generated dashboard is Red-Queen-managed, uses native Home Assistant cards and native Red Queen entities, and never exposes provider entities directly.

## Architecture

```text
Red Queen Registry
        ↓
House domain model
        ↓
DashboardModel
        ↓
Native entity binding
        ↓
Lovelace renderer
        ↓
Red Queen dashboard
```

The semantic model and Lovelace implementation are intentionally separated. The dashboard model does not know Home Assistant entity IDs or storage details.

## Generated views

The first RC12 dashboard contains:

1. Overview
2. One main view per floor
3. One subview per room
4. Plants view when plants exist
5. Red Queen system/diagnostic view

Rooms without a usable floor assignment must remain visible through a deterministic fallback floor instead of being discarded.

## Overview

The overview may contain:

- House status
- Openings
- Lighting
- Covers
- Garage
- Plants
- Security
- Red Queen status

Optional feature cards appear only when that feature exists. House status and Red Queen status remain available independent of optional house functions.

## Main actions

The overview may expose:

- global Red Queen lighting-off action;
- every configured door-release action;
- every configured garage-door control.

The dashboard never reimplements safety logic. All physical actions continue through native Red Queen entities and canonical execution guards.

## Floor views

A floor view shows compact room cards. Each room card summarizes relevant state such as:

- open openings;
- unlocked access;
- lights on;
- cover errors;
- cover movement;
- closed/intermediate covers.

Selecting a room navigates to its room subview. RC12 does not create UI helper entities for navigation.

## Room subviews

A room may contain these blocks:

1. Lighting
2. Openings
3. Access
4. Covers
5. Plants

Missing features are omitted completely; empty placeholder cards are not generated.

## Native-only binding

Dashboard generation binds semantic Red Queen objects to their native Home Assistant entities. Provider entities such as PLC/OPC UA/MQTT feedback and command entities are not written into the generated dashboard.

Entity-ID changes are handled by resolving bindings again whenever the dashboard is refreshed. The stable identity remains the Red Queen semantic ID / native unique ID contract.

## Covers

- Open/close are shown only through the native Red Queen cover entity.
- Read-only position is shown only when objective position feedback exists.
- Blade-open/blade-close controls appear only when both blade capabilities exist.
- No arbitrary set-position control is invented.
- Existing native availability and canonical safety guards remain authoritative.

## Access and garage

- Opening state is shown through native Red Queen opening entities.
- Lock controls appear only when a native lock exists.
- Door release appears only when configured.
- Garage controls use the native garage cover and its guarded open/close/stop feature availability.
- An intermediate garage state never causes the dashboard to guess a direction.

## Plants

- Plant Care status is shown through the native Red Queen Plant Care sensor.
- Watering is recorded through the native watering button.
- The dashboard does not claim physical irrigation.
- Plants view ordering prioritizes `overdue`, `due`, `unknown`, then `ok`.

## Lifecycle

The configurator will eventually provide:

- Dashboard status
- Create dashboard
- Refresh dashboard

Registry mutation does not silently rewrite the dashboard in RC12. A refresh is explicit.

Refresh must be idempotent: the same registry and entity bindings produce the same logical dashboard.

## Ownership and safety

Red Queen must not overwrite the user's existing dashboards. The generated dashboard has explicit Red Queen ownership and a stable dedicated URL path.

The integration must not manipulate `.storage` files directly. The Home Assistant adapter will isolate dashboard persistence behind a dedicated compatibility boundary.

## RC12 scope

Included:

- dashboard model;
- native entity binding;
- overview;
- floor views;
- room subviews;
- lighting;
- covers;
- openings/access;
- garage;
- plants;
- system view;
- configurator create/refresh;
- native Home Assistant cards.

Not included:

- weather/environment;
- climate;
- media;
- cameras;
- energy;
- custom dashboard designer;
- custom Lovelace cards;
- Mushroom/card-mod/stack-in-card dependencies;
- separate mobile/tablet profiles.

## Acceptance gate

A fresh test installation must be able to commission a managed Red Queen registry and create a complete usable dashboard without manual Lovelace YAML.

Mandatory regression checks include:

- no custom cards required;
- no provider entities in generated dashboard configuration;
- no UI navigation helpers created;
- no existing user dashboard modified;
- dashboard survives Home Assistant restart;
- refresh is idempotent;
- added registry objects appear after refresh;
- removed registry objects disappear after refresh;
- unavailable native entities remain visible;
- canonical safety guards remain effective;
- Red Queen registry remains unchanged by dashboard generation.
