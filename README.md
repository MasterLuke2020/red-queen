# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house
as semantic objects and state, evaluates context/rules/policies/decisions, resolves
capabilities and providers, and executes explicitly supported actions through
contracts and feedback-aware guards.

> **Current candidate:** `1.0.0-rc9` — LIVE VERIFIED<br>
> **Technical Home Assistant domain:** `wnhf`<br>
> **Development lineage:** WNHF `1.35.0` / `WP-4.7.15.0`

## RC9 candidate changes

- Preserves the live-verified RC8 device and notification contracts.
- Adds optional semantic `plants.yaml` registry support.
- Adds `plants.snapshot` and canonical `plants.record_watering`.
- Persists watering history atomically and exposes one dashboard sensor plus one
  native record-watering button per plant, attached to its Red Queen room device.
- Starts plants at `unknown` until a real watering event is recorded.
- Qualifies the persistent state change without claiming physical watering or soil
  moisture observation.

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

`1.0.0-rc9` and WP-4.7.15.0 preserve the live-verified RC8 baseline. Static and live
qualification of the new Plant Care domain passed on 2026-08-21.

See `docs/RC9_CANDIDATE_VALIDATION.md` for the qualification plan.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home
Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Registry data under `/config/wnhf` is installation-specific and is intentionally not
part of the integration source tree.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
