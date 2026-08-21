# Release Status

## Current candidate

**Red Queen 1.0.0-rc8 — LIVE VERIFIED**

RC8 is based on the published, live-verified RC7 baseline and adds WP-4.7.14.0
Canonical Cover Blades / Electric Door Release. Existing lighting, directional cover,
garage, door lock/unlock and notification behavior is intentionally preserved.

The inherited RC7 reference-installation baseline passed on 2026-08-20 with:

- `status: healthy`
- `runtime_ready: true`
- `health_score: 100`
- `error_count: 0`
- `warning_count: 0`

RC8 live qualification passed on 2026-08-21 and verified:

- blade open and blade close on one reference venetian blind;
- moving-cover rejection without a blade pulse;
- confirmed courtyard and street door-opener dispatch with one physical pulse each;
- missing-confirmation and open-door rejection without a pulse;
- dispatch-scoped evidence with `hardware_verified: false` for blades and release;
- final health 100 with no Red Queen errors or warnings.

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
