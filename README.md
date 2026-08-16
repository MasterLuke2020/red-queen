# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house as semantic objects and state, evaluates context/rules/policies/decisions, resolves capabilities and providers, and executes explicitly supported actions through contracts and feedback-aware guards.

> **Current candidate:** `1.0.0-rc5` — LIVE VERIFIED on the reference installation
> **Technical Home Assistant domain:** `wnhf`
> **Development lineage:** WNHF `1.31.0` / `WP-4.7.12.1`

## RC5 candidate changes

- Adds a first-class semantic `garage` capability with `garage.snapshot`, `garage.open`, and `garage.close`.
- Promotes `garage.open` and `garage.close` into canonical real execution.
- Both directional actions require explicit `confirmed: true`.
- Residential OSC control is abstracted behind semantic directions:
  - already at requested end position → no OSC pulse (`EXE-101`);
  - proven opposite end position → exactly one OSC pulse and feedback observation;
  - moving state → reject without a pulse;
  - intermediate position → reject without a pulse because the next OSC direction is ambiguous;
  - contradictory or unavailable end-position feedback → reject without a pulse;
  - command sent without confirmed requested end position → `EXE-301`.
- Canonical garage stop/toggle is intentionally not exposed. The technical OSC capability remains internal.
- Existing canonical lighting, covers, and door lock/unlock behavior remains unchanged.

## Current canonical real-execution surface

```text
lighting.turn_on
lighting.turn_off
covers.open
covers.close
garage.open
garage.close
openings.lock
openings.unlock
```

Canonical execution entry point: `wnhf.execution_execute`
Dry-run entry point: `wnhf.execution_dry_run`

## Candidate status

`1.0.0-rc5` has passed local static and isolated behavior validation. Live Home Assistant verification is still required before the work package is marked LIVE VERIFIED and before repository tagging/publishing.

See `docs/RC5_CANDIDATE_VALIDATION.md` for the validation record and live test plan.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Registry data under `/config/wnhf` is installation-specific and is intentionally not part of the integration source tree.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
