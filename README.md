# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house
as semantic objects and state, evaluates context/rules/policies/decisions, resolves
capabilities and providers, and executes explicitly supported actions through
contracts and feedback-aware guards.

> **Current candidate:** `1.0.0-rc6` — LIVE VERIFIED on the reference installation<br>
> **Technical Home Assistant domain:** `wnhf`<br>
> **Development lineage:** WNHF `1.32.0` / `WP-4.7.13.1`

## RC6 candidate changes

- Adds the provider-neutral `notifications` capability with
  `notifications.snapshot` and canonical `notifications.send`.
- Resolves semantic notification targets through `provider.core.notifications` and
  Home Assistant `notify.send_message` entities.
- Requires a non-empty `message`; accepts an optional string or null `title`.
- Does not require confirmation and is intentionally non-idempotent: identical
  requests are separate sends.
- Qualifies successful notification execution at `dispatch` scope only:
  `framework_verified: true`, `hardware_verified: false`.
- Never claims handset delivery or read receipt and never persists message/title text
  in execution qualification evidence.
- Preserves all previously verified lighting, cover, garage and lock contracts.

Announcements/TTS, context routing, priority/category handling and arbitrary
provider-specific data are deliberately deferred.

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
notifications.send
```

Canonical execution entry point: `wnhf.execution_execute`<br>
Dry-run entry point: `wnhf.execution_dry_run`

## Candidate status

`1.0.0-rc6` and WP-4.7.13.1 passed static, isolated and live Home Assistant
validation on the reference installation on 2026-08-17. Final runtime health was
100 with zero errors and zero warnings.

See `docs/RC6_CANDIDATE_VALIDATION.md` for the validation record.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home
Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Registry data under `/config/wnhf` is installation-specific and is intentionally not
part of the integration source tree.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
