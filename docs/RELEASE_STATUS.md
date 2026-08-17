# Release Status

## Current candidate

**Red Queen 1.0.0-rc6 — LIVE VERIFIED / PUBLICATION PENDING**

RC6 is based on the released RC5 baseline and adds WP-4.7.13.1 Semantic
Notifications Core. Existing lighting, cover, garage and door lock/unlock canonical
behavior is intentionally preserved. WP-4.7.13.1 passed live reference-installation
verification on 2026-08-17.

Final observed runtime state:

- `status: healthy`
- `runtime_ready: true`
- `health_score: 100`
- `error_count: 0`
- `warning_count: 0`

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
