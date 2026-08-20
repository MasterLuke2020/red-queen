# RC7 Candidate Validation Record

Validation state: **LIVE VERIFIED — 2026-08-20**<br>
Work package: WP-4.7.13.2 — Native Notification Routing / Announcements<br>
Development baseline: WNHF 1.33.0<br>
Public candidate: Red Queen 1.0.0-rc7<br>
Canonical API: 1.0

## Static acceptance — passed

- Python and YAML syntax pass.
- Seven capabilities and seventeen unique semantic actions.
- Eleven canonical real-execution contracts.
- Existing physical-device and `notifications.send` contracts unchanged.
- Registry loader accepts the reference announcement/route configuration and rejects
  malformed IDs, entity domains, enum values, volumes and references.
- Qualification evidence remains dispatch-scoped and stores no message/title body.

## Live environment and candidate correction

- Home Assistant reference house: `Weidnerhome`.
- Red Queen `1.0.0-rc7`, WNHF `1.33.0`, WP-4.7.13.2.
- Release phase label corrected to `Release Candidate 7` before functional tests.
- Initial framework-managed Sonos snapshot/restore caused one additional playback
  interruption after music had already resumed.
- The corrected provider uses a TTS Media Source through
  `media_player.play_media`, `announce: true` and `extra.volume`; Sonos owns overlay
  restoration and Red Queen sends no second snapshot or restore command.
- Repository verification and isolated notification-provider tests passed after the
  correction.

## Live preflight and guards — passed

| Test | Result | Dispatch |
|---|---|---|
| Valid Office announcement dry-run | `EXE-100` | none |
| Empty message dry-run | `EXE-204` | none |
| Empty message real surface | `EXE-206` | none |
| Invalid announcement level | `EXE-204` | none |
| Unknown semantic announcement target | `EXE-203` | none |
| Raw `media_player.office` target | `EXE-203` | none |
| Invalid route priority and profile | `EXE-204` | none |

The public envelope exposed no raw TTS entity, speaker list or notify entity. Every
rejection occurred before provider dispatch and produced no qualification evidence.

## Native announcements — passed

| Target | Level | Observed result |
|---|---|---|
| `announcement.target.office` | `info` | Office only, no prefix, volume 0.35, `EXE-000` |
| `announcement.target.office` | `notice` | `Hinweis.`, volume 0.35, `EXE-000` |
| `announcement.target.office` | `warning` | `Warnung.`, volume 0.45, `EXE-000` |
| `announcement.target.office` | `alarm` | `Achtung!`, volume 0.55, `EXE-000` |
| `announcement.target.house` | `info` | All five configured Sonos speakers, `EXE-000` |

Existing music was overlaid and resumed once without the earlier second
interruption. The native result reported `restore_strategy: sonos_native_announce`,
`restore_completed_by_framework: false` and dispatch-scoped verification. Persistent
qualification recorded eight successful announcement executions with
`framework_verified: true` and `hardware_verified: false`.

## Native routing — passed

| Profile/context | Selected behavior | Observed result |
|---|---|---|
| `silent`, warning | log/dashboard/mobile; no voice | all selected channels succeeded |
| `standard`, warning, home/quiet off | log/dashboard/mobile/voice | all four succeeded |
| `voice`, warning | log/dashboard/voice; no mobile | all selected channels succeeded |
| `mobile`, info | log/mobile only | both channels succeeded |
| `broadcast`, critical | all four channels; alarm voice | broadcast override set |
| `standard`, warning, quiet on | log/dashboard/mobile; voice suppressed | context guard passed |
| `broadcast`, warning, quiet on | all four channels including voice | context override passed |
| `standard`, debug | dashboard skipped by priority; notice voice | `debug → notice` passed |
| `standard`, info | dashboard skipped by priority; info voice | `info → info` passed |

The `warning → warning` and `critical → alarm` mappings were also heard and confirmed.
Warning/critical dashboard routes created persistent notifications; debug/info
dashboard results returned `skipped_priority` and created none. Mobile notifications
arrived, and Activity entries were present under `sensor.wnhf_house_state`.
Persistent qualification recorded ten successful route executions with
`framework_verified: true` and `hardware_verified: false`.

The externally calculated `sensor.wnhf_house_state` immediately restored its real
`home_evening` value when a temporary state was attempted. The house-state block was
therefore not artificially forced; the shared voice-context suppression branch and
broadcast override were live exercised through Quiet Mode instead.

## Compatibility regression — passed

- Direct RC6 `notifications.send` returned `EXE-000`, arrived on the configured
  phone and advanced its persistent pass count to 3.
- `lighting.turn_off` dry-run for `light.eg.kitchen.spots`: `EXE-100`, no command.
- `covers.open` dry-run for `cover.eg.bathroom_wc.main`: `EXE-100`, no command.
- Confirmed `garage.open` dry-run for `opening.outdoor.garage.main_door`:
  `EXE-100`, no command.
- Confirmed `openings.unlock` dry-run for
  `opening.eg.vestibule.door.courtyard`: `EXE-100`, no command.

## Final health and qualification

- Runtime status: healthy and ready; health score 100.
- 17 of 17 semantic actions ready; 11 of 11 real actions executable.
- Seven providers healthy; zero invalid, unavailable or unhealthy providers.
- Qualification store loaded, persistent and healthy with 17 evidence records.
- Final notification pass counts: send 3, announce 8, route 10.
- Persistent evidence stores no notification message, title or spoken body.
- Scheduler: zero active locks and zero queued transactions.
- Global system status: zero Red Queen errors and zero warnings.
- Final Home Assistant log review: no Red Queen errors or warnings.

**Red Queen 1.0.0-rc7 / WP-4.7.13.2 is LIVE VERIFIED.**
