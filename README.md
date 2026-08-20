# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house
as semantic objects and state, evaluates context/rules/policies/decisions, resolves
capabilities and providers, and executes explicitly supported actions through
contracts and feedback-aware guards.

> **Current candidate:** `1.0.0-rc7` — LIVE VERIFIED / RELEASE PREPARATION READY<br>
> **Technical Home Assistant domain:** `wnhf`<br>
> **Development lineage:** WNHF `1.33.0` / `WP-4.7.13.2`

## RC7 candidate changes

- Preserves the live-verified RC6 `notifications.send` contract.
- Adds native canonical `notifications.announce` with provider-neutral announcement
  targets, four urgency levels and Sonos-native announce overlays.
- Adds canonical `notifications.route` with the original WNHF priority/profile
  channel matrix for log, dashboard, mobile and voice.
- Replaces the historical `notify_house` script and WNHF channel automations with
  native Red Queen provider execution; they are not runtime dependencies.
- Keeps raw TTS, media-player and mobile entity IDs in installation registry data.
- Qualifies successful notification execution at dispatch scope only and never
  claims delivery, read receipt or audible playback.
- Preserves all previously verified lighting, cover, garage and lock contracts.

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
notifications.announce
notifications.route
```

Canonical execution entry point: `wnhf.execution_execute`<br>
Dry-run entry point: `wnhf.execution_dry_run`

## Candidate status

`1.0.0-rc7` and WP-4.7.13.2 were live verified on the reference Home Assistant
installation on 2026-08-20. Native Sonos announcements, all routing profiles and
priorities, context guards, request guards, direct notification compatibility and
physical-action dry-run regressions passed. Final runtime health was 100 with zero
Red Queen errors or warnings.

See `docs/RC7_CANDIDATE_VALIDATION.md` for the observed validation record.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home
Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Registry data under `/config/wnhf` is installation-specific and is intentionally not
part of the integration source tree.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
