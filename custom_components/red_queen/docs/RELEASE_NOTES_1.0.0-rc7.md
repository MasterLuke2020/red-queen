# Red Queen 1.0.0-rc7

## WP-4.7.13.2 — Native Notification Routing / Announcements

RC7 promotes the original WNHF notification and house-announcement prototypes into
native, provider-neutral Red Queen execution.

- canonical `notifications.announce`;
- canonical `notifications.route`;
- semantic announcement targets with installation-owned TTS/speaker mappings;
- `info`, `notice`, `warning` and `alarm` announcement levels;
- `debug`, `info`, `warning` and `critical` routing priorities;
- `standard`, `silent`, `voice`, `mobile` and `broadcast` routing profiles;
- native Home Assistant TTS dispatch;
- Sonos-native `announce` overlays with automatic playback/volume restoration;
- serialized announcements per semantic target;
- context-guarded voice routing with explicit broadcast override;
- log, dashboard, mobile and voice channel results in one canonical response;
- persistent dashboard notifications for `warning` and `critical` routes;
- strict rejection of empty messages, invalid enums and raw provider entity IDs in
  the public action envelope.

The legacy `script.notify_house`, `WNHF Notify` script and WNHF channel automations
are reference prototypes only. RC7 does not call them and does not require them.

Sonos announcement targets use a TTS Media Source through
`media_player.play_media`, `announce: true` and `extra.volume`. Sonos owns overlay
restoration; Red Queen sends no second snapshot/restore command. Successful
announcement execution proves accepted dispatch only. It does not claim that audio
was audible, heard by a resident or that restoration completion was independently
observed.
Successful mobile routing remains dispatch-scoped and does not claim delivery/read.

## Compatibility

The RC6 `notifications.send` contract and all previously qualified lighting, cover,
garage and lock/unlock contracts remain unchanged. The canonical service remains
`wnhf.execution_execute`; the technical integration domain remains `wnhf`.

## Live qualification

WP-4.7.13.2 was live verified on the reference Home Assistant installation on
2026-08-20:

- valid announcement dry-run: `EXE-100`;
- all four Office levels and the five-speaker house target: `EXE-000`;
- native Sonos overlay restored music exactly once without a second interruption;
- all five routing profiles and all four priority mappings passed;
- Quiet Mode voice suppression and broadcast override passed;
- mobile, persistent dashboard and Activity channels were observed;
- empty-message, enum, unknown-target and raw-entity guards rejected before dispatch;
- direct RC6 notification dispatch and lighting/cover/garage/opening regressions
  passed;
- final notification evidence: send pass count 3, announce 8, route 10;
- final runtime health: 100, runtime ready, zero Red Queen errors and zero warnings.

**Red Queen 1.0.0-rc7 / WP-4.7.13.2 is LIVE VERIFIED.**
