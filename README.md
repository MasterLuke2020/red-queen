# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house
as semantic objects and state, evaluates context/rules/policies/decisions, resolves
capabilities and providers, and executes explicitly supported actions through
contracts and feedback-aware guards.

> **Current candidate:** `1.0.0-rc8` — LIVE VERIFIED<br>
> **Technical Home Assistant domain:** `wnhf`<br>
> **Development lineage:** WNHF `1.34.0` / `WP-4.7.14.0`

## RC8 candidate changes

- Preserves the live-verified RC7 notification, lighting, directional cover,
  garage and lock contracts.
- Promotes the existing venetian-blind commands to canonical
  `covers.blades_open` and `covers.blades_close` execution.
- Adds confirmed canonical `openings.release` execution for configured electric
  door openers.
- Treats blade and door-opener success honestly as dispatch-scoped: Red Queen
  records successful command dispatch without claiming an unobservable blade
  position, latch release or physical door opening.
- Blocks blade commands while the cover is moving and blocks door release unless
  the semantic door is proven closed.

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
```

Canonical execution entry point: `wnhf.execution_execute`<br>
Dry-run entry point: `wnhf.execution_dry_run`

## Candidate status

`1.0.0-rc8` and WP-4.7.14.0 preserve the live-verified RC7 baseline. Static
repository verification and controlled blade/door-opener live qualification passed
on the reference Home Assistant installation on 2026-08-21.

See `docs/RC8_CANDIDATE_VALIDATION.md` for the qualification plan and observed results.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home
Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Registry data under `/config/wnhf` is installation-specific and is intentionally not
part of the integration source tree.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
