# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house as semantic objects and state, evaluates context/rules/policies/decisions, resolves capabilities and providers, and executes explicitly supported actions through contracts and feedback-aware guards.

> **Current candidate:** `1.0.0-rc3` — LIVE VERIFIED candidate  
> **Technical Home Assistant domain:** `wnhf`  
> **Development lineage:** WNHF `1.29.1` / `WP-4.7.10.2`

## RC3 candidate changes

- Added canonical `covers.open` and `covers.close` real execution.
- Added symmetric feedback guards for cover end states and movement:
  - requested end state already satisfied → no hardware command (`EXE-101`);
  - requested movement already active → no duplicate command (`EXE-102`);
  - opposite movement active → reject without automatic reversal;
  - stable opposite/intermediate state → one command and feedback confirmation (`EXE-000`).
- Cover `OPEN` and `CLOSED` feedback now represent true physical end positions.
- Added optional `feedback.closed_percent_entity_id` for continuous cover position feedback.
- Native Home Assistant cover position is derived as `100 - ClosedPercent`.
- Position remains read-only; `SET_POSITION` is not advertised because no target-position command exists.
- Existing lighting canonical execution from RC2 remains unchanged.

## Current canonical real-execution surface

```text
lighting.turn_on
lighting.turn_off
covers.open
covers.close
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

`1.0.0-rc3` has passed live validation on the reference installation, including cover position feedback and guarded canonical OPEN/CLOSE execution. It is not considered published until the repository branch passes Static repository checks and Home Assistant hassfest and a `v1.0.0-rc3` tag/release is created.

See `docs/RC3_CANDIDATE_VALIDATION.md` for the validation record.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Registry data under `/config/wnhf` is installation-specific and is intentionally not part of the integration source tree.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
