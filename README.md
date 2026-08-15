# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house as semantic objects and state, evaluates context/rules/policies/decisions, resolves capabilities and providers, and executes explicitly supported actions through contracts and feedback-aware guards.

> **Current candidate:** `1.0.0-rc4` — LIVE VERIFIED candidate  
> **Technical Home Assistant domain:** `wnhf`  
> **Development lineage:** WNHF `1.30.0` / `WP-4.7.11.1`

## RC4 candidate changes

- Added canonical `openings.lock` and `openings.unlock` real execution.
- Both actions require explicit `confirmed: true`.
- Added guarded lock/unlock execution using the existing Access object contract:
  - requested lock state already satisfied → no hardware command (`EXE-101`);
  - valid opposite lock state → one command and feedback confirmation (`EXE-000`);
  - open door → reject without sending a lock command;
  - unavailable or invalid lock feedback → reject without command;
  - missing explicit confirmation → reject (`EXE-202`).
- Existing canonical lighting and cover execution from RC2/RC3 remains unchanged.
- Door-opener and garage commands are intentionally not promoted by this candidate.

## Current canonical real-execution surface

```text
lighting.turn_on
lighting.turn_off
covers.open
covers.close
openings.lock
openings.unlock
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

`1.0.0-rc4` has passed live validation on the reference installation, including confirmation gating, real lock/unlock execution, idempotency, the open-door safety guard, and a second physical door regression.

It is not considered published until the repository branch passes Static repository checks and Home Assistant hassfest and a `v1.0.0-rc4` tag/release is created.

See `docs/RC4_CANDIDATE_VALIDATION.md` for the validation record.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Registry data under `/config/wnhf` is installation-specific and is intentionally not part of the integration source tree.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
