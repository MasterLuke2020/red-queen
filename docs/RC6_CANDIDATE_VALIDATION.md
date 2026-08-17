# Red Queen 1.0.0-rc6 Candidate Validation

Validation date: 2026-08-17<br>
Work package: WP-4.7.13.1 — Semantic Notifications Core<br>
Development baseline: WNHF 1.32.0<br>
Public candidate: Red Queen 1.0.0-rc6<br>
Canonical API: 1.0<br>
Canonical dry-run contract: 1.7-rc6<br>
Canonical real-execution contract: 1.8-rc6

## Scope

RC6 adds:

- semantic `notifications` capability;
- `notifications.snapshot`;
- canonical `notifications.send`;
- provider-owned `notification_targets.yaml` registry;
- `provider.core.notifications` using Home Assistant `notify.send_message`;
- required canonical parameter keys;
- dispatch-scoped execution and qualification evidence.

Announcements/TTS, routing by context/resident, priority/category and arbitrary
provider data are not part of this packet.

## Request and execution contract

`notifications.send` targets exactly one semantic `notification.target.*` object.

Parameters:

- `message`: required, string, non-empty after trimming;
- `title`: optional, string or null;
- all other keys: rejected.

Confirmation is not required. Sends are non-idempotent; identical requests are
separate dispatches and must not return `EXE-101`.

## Verification semantics and privacy

Successful `notify.send_message` completion proves framework dispatch only:

- `verification_scope: dispatch`;
- `framework_verified: true`;
- `hardware_verified: false`;
- `delivery_receipt_claimed: false`;
- `read_receipt_claimed: false`.

Persistent qualification evidence contains no message or title text. Evidence merging
preserves the existing verification flags and cannot promote dispatch-only evidence
to hardware-verified.

## Static validation expectations

- manifest `1.0.0-rc6`;
- release baseline `WP-4.7.13.1` / WNHF `1.32.0`;
- dry-run/real contracts `1.7-rc6` / `1.8-rc6`;
- Execution Manager marker `1.6-rc6`;
- 66 Home Assistant services;
- 7 capability definitions;
- 15 semantic actions;
- 9 canonical real-execution contracts;
- notifications active in release scope;
- LF-normalized source checksum verification.

## Live Home Assistant verification

**LIVE VERIFIED — 2026-08-17**

1. Release info reported Red Queen `1.0.0-rc6`, WNHF `1.32.0`,
   `WP-4.7.13.1`, canonical API `1.0` and real contract `1.8-rc6`.
2. Execution Manager reported 7 capabilities, 15 declared/semantically-ready
   actions and 9 real/executable actions.
3. Provider diagnostics reported 7 providers, all healthy, available and
   contract-valid, with zero warnings/errors.
4. Notification provider reported one configured, enabled and available semantic
   target and `notify_send_message_available: true`.
5. Valid dry-run returned `EXE-100` without dispatch.
6. Empty message rejected with `EXE-204`.
7. Unknown semantic target rejected with `EXE-203`.
8. First real send returned `EXE-000` and arrived on the reference phone.
9. The identical second request also returned `EXE-000` and arrived, proving
   non-idempotency.
10. Qualification stored `real_success` with pass count 2,
    `framework_verified: true` and `hardware_verified: false`.
11. Persistent evidence contained no notification message/title text.
12. Final system status: healthy, runtime ready, health score 100, zero errors,
    zero warnings, zero active/queued transactions.
13. Final qualification: overall pass with automatic collection and persistence
    enabled.

**WP-4.7.13.1 is LIVE VERIFIED.**

## Source provenance

The live-tested runtime source came from
`Red_Queen_1.0.0-rc6_Candidate_WP-4.7.13.1.zip`.

Candidate SHA-256:

`82bb45adf51e3ea7dbce5b853782f9764f3ed49395e2588397169208c4af923d`

The release-branch package preserves that runtime source except for the documented
internal manager-version cleanup and release documentation metadata.
