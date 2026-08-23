# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house
as semantic objects and state, evaluates context/rules/policies/decisions, resolves
capabilities and providers, and executes explicitly supported actions through
contracts and feedback-aware guards.

> **Current candidate:** `1.0.0-rc11` — LIVE VERIFIED<br>
> **Technical Home Assistant domain:** `wnhf`<br>
> **Development lineage:** WNHF `1.37.0` / `WP-4.7.17.0`

## RC11 candidate changes

RC11 turns the existing semantic registry foundation into a guided Home Assistant
commissioning path for the currently supported house model.

- Adds explicit `uninitialized`, `manual` and `managed` registry ownership modes.
- Adds managed base creation from Home Assistant Areas/Floors.
- Generates semantic IDs automatically for configurator-created rooms and objects.
- Adds guided configuration for rooms, impulse lights, venetian blinds, windows,
  sliding doors, doors, garage doors and Plant Care.
- Adds transaction staging, backups and rollback for managed registry writes.
- Preserves existing manual registries as read-only.
- Adds canonical `garage.stop` when a dedicated STOP command is configured.
- Keeps cover positioning read-only and blade commands explicit.
- Adds localized configurator validation and native-action guard messages.

## Current canonical real-execution surface

```text
lighting.turn_on
lighting.turn_off
covers.open
covers.close
covers.blades_open
covers.blades_close
garage.open
garage.close
garage.stop
openings.lock
openings.unlock
openings.release
notifications.send
notifications.announce
notifications.route
plants.record_watering
```

Canonical execution entry point: `wnhf.execution_execute`<br>
Dry-run entry point: `wnhf.execution_dry_run`

## Candidate status

The exact consolidated RC11 package was installed and live-regression-tested on the
dedicated Home Assistant test system on 2026-08-22. Managed configuration, native
light/cover/access/garage behavior, Plant Care persistence, localized guards and
restart persistence passed. Home Assistant hassfest passed on the RC11 release branch
on 2026-08-23. Publication still requires the final repository static check on the
release commit.

See `docs/RC11_CANDIDATE_VALIDATION.md` and
`custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc11.md`.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home
Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Installation-owned data remains below `/config/wnhf`. Existing manual registries are
not silently adopted or rewritten by the RC11 configurator.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
