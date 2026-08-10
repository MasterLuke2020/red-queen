# Release Status

## Current public candidate

**Red Queen 1.0.0-rc1 — LIVE VERIFIED**

The release candidate is cut from the live-verified WNHF 1.27.0 / WP-4.7.9.1 baseline. The RC packaging changed product identity, release metadata, visible naming and documentation. The previously verified execution/provider/feedback/qualification architecture was intentionally not redesigned.

## RC freeze policy

During the RC phase:

- no new smart-home domain is added to `1.0.0-rc1`;
- no new canonical mutating action is added to RC1;
- functional defects are fixed in a new candidate (for example `1.0.0-rc2`);
- the verified RC1 archive is never silently overwritten;
- new feature development resumes after the stable 1.0 release line is established.

## Technical identity

The Home Assistant integration domain and service namespace remain `wnhf`. This is an intentional compatibility boundary and is not the public product name.

## Stable public execution entry

`wnhf.execution_execute` is the canonical productive execution entry. `wnhf.execute` is a legacy Decision-ID compatibility path and is not recommended for new automations.
