# Release Status

## Current candidate

**Red Queen 1.0.0-rc7 — LIVE VERIFIED / RELEASE PREPARATION READY**

RC7 is based on the published, live-verified RC6 baseline and adds WP-4.7.13.2 Native
Notification Routing / Announcements. Existing lighting, cover, garage, door
lock/unlock and direct notification behavior is intentionally preserved.

Reference-installation live qualification passed on 2026-08-20 with:

- `status: healthy`
- `runtime_ready: true`
- `health_score: 100`
- `error_count: 0`
- `warning_count: 0`

- all four announcement levels on Office and five-speaker house targets;
- all five routing profiles and all four priority-to-voice mappings;
- Quiet Mode suppression and broadcast override;
- direct RC6 notification compatibility plus physical-action dry-run regressions;
- persistent dispatch-scoped evidence for notification send, announce and route;
- no Red Queen errors or warnings after the completed test sequence.

## RC policy

During the RC line, capability additions are accepted only as bounded work packages
with explicit contracts, static validation, isolated behavior validation, live Home
Assistant validation, regression checks and a new immutable release candidate. A
previously published RC is never silently overwritten.

## Technical identity

The Home Assistant integration domain and service namespace remain `wnhf`. This is
an intentional compatibility boundary and is not the public product name.

## Stable public execution entry

`wnhf.execution_execute` is the canonical productive execution entry.
`wnhf.execute` is a legacy Decision-ID compatibility path and is not recommended for
new automations.
