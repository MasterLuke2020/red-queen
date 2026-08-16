# Release Status

## Current candidate

**Red Queen 1.0.0-rc5 — LIVE VERIFIED / PUBLICATION PENDING**

RC5 is based on the live-verified RC4 baseline and adds WP-4.7.12.1 canonical
residential garage open/close execution. Existing lighting, cover, and door lock/unlock
canonical behavior is intentionally preserved. WP-4.7.12.1 passed live reference-installation verification on 2026-08-16.

## RC policy

During the RC line, capability additions are accepted only as bounded work packages
with explicit contracts, static validation, isolated behavior validation, live Home
Assistant validation, regression checks, and a new immutable release candidate. A
previously published RC is never silently overwritten.

## Technical identity

The Home Assistant integration domain and service namespace remain `wnhf`. This is an
intentional compatibility boundary and is not the public product name.

## Stable public execution entry

`wnhf.execution_execute` is the canonical productive execution entry.
`wnhf.execute` is a legacy Decision-ID compatibility path and is not recommended for
new automations.
