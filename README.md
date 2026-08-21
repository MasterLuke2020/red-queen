# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house
as semantic objects and state, evaluates context/rules/policies/decisions, resolves
capabilities and providers, and executes explicitly supported actions through
contracts and feedback-aware guards.

> **Current candidate:** `1.0.0-rc10` — LIVE VERIFIED<br>
> **Technical Home Assistant domain:** `wnhf`<br>
> **Development lineage:** WNHF `1.36.0` / `WP-4.7.16.0`

## RC10 candidate changes

- Preserves the published, live-verified RC9 semantic and execution contracts.
- Adds one room-associated native state entity for every enabled opening.
- Adds native room controls for motor locks, electric door release and the garage
  door, plus explicit blade-open/blade-close buttons for every capable blind.
- Routes native light, cover, blade, lock, door-release, garage and Plant Care
  controls through the canonical execution service.
- Keeps central health, security and aggregate diagnostics on their existing module
  devices while placing physical object state and controls in their semantic rooms.

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

`1.0.0-rc10` and WP-4.7.16.0 preserve the published, live-verified RC9 baseline.
Static and reference-installation live qualification passed on 2026-08-21.

See `docs/RC10_CANDIDATE_VALIDATION.md` for the qualification plan.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home
Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Registry data under `/config/wnhf` is installation-specific and is intentionally not
part of the integration source tree.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
