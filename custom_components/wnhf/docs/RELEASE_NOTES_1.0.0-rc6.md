# Red Queen 1.0.0-rc6

## WP-4.7.13.1 — Semantic Notifications Core

RC6 adds the first provider-neutral semantic notification capability.

- `notifications.snapshot`
- canonical `notifications.send`
- optional `/config/wnhf/house/registry/notification_targets.yaml`
- `provider.core.notifications`
- required non-empty `message`, optional string/null `title`
- no confirmation requirement
- non-idempotent dispatch
- dispatch-scoped qualification
  (`framework_verified: true`, `hardware_verified: false`)
- no persistent message/title in qualification evidence

A successful canonical notification proves completion of the Home Assistant
`notify.send_message` service call. It does not claim remote-device delivery or that
a resident read it.

The evidence merge path preserves verification flags, preventing dispatch-only
evidence from being promoted to hardware-verified.

Deferred: TTS/announcements, priority/category routing, presence/resident routing and
provider-specific arbitrary notification data.

## Compatibility

The existing canonical lighting, cover, garage and lock/unlock contracts are
unchanged. The canonical service remains `wnhf.execution_execute`; the technical
integration domain remains `wnhf`.

## Verification

WP-4.7.13.1 was live verified on the reference installation on 2026-08-17:

- valid dry-run: `EXE-100`;
- empty-message guard: `EXE-204`;
- unknown-target guard: `EXE-203`;
- two identical real sends: `EXE-000` twice, both received;
- notification qualification: real-success pass count 2, framework verified,
  hardware not verified;
- final runtime health: 100, runtime ready, zero errors and zero warnings.

**Red Queen 1.0.0-rc6 / WP-4.7.13.1 is LIVE VERIFIED.**
