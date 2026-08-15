# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house as semantic objects and state, evaluates context/rules/policies/decisions, resolves capabilities and providers, and executes explicitly supported actions through contracts and feedback-aware guards.

> **Current candidate:** `1.0.0-rc2` — LIVE VERIFIED candidate  
> **Technical Home Assistant domain:** `wnhf`  
> **Development lineage:** WNHF `1.28.0` / `WP-4.7.10.1`

## RC2 candidate changes

- Fixed Home Assistant response semantics for `wnhf.execution_execute`: the mutating service now supports optional responses and can be called directly from dashboards without a wrapper script.
- Added canonical `lighting.turn_on` real execution alongside `lighting.turn_off`.
- Both lighting directions use feedback-guarded idempotent momentary execution:
  - target state already satisfied → no hardware command (`EXE-101`);
  - opposite state → one command pulse and feedback confirmation (`EXE-000`).
- Existing `wnhf` domain, service IDs, registry/config paths and qualification persistence remain compatible.

## Current canonical lighting surface

```text
lighting.turn_on
lighting.turn_off
```

Canonical execution entry point:

```text
wnhf.execution_execute
```

Dry-run entry point:

```text
wnhf.execution_dry_run
```

## Candidate status

`1.0.0-rc2` has passed live validation on the reference installation. It is not considered published until the repository branch passes Static repository checks and Home Assistant hassfest and a `v1.0.0-rc2` tag/release is created.

See `docs/RC2_CANDIDATE_VALIDATION.md` for the validation record.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
