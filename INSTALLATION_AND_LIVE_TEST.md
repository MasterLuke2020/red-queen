# Red Queen 1.0.0-rc7 — Installation and live qualification

Status: live verified for WP-4.7.13.2 on 2026-08-20. Publication still requires the
repository, CI, tag and GitHub web release steps from `PUBLISHING_CHECKLIST.md`.

## 1. Back up the current installation

Back up these paths before replacing anything:

- `/config/custom_components/wnhf`
- `/config/wnhf/house/registry/notification_targets.yaml`, if present

The historical `script.notify_house`, `WNHF Notify` script and the three channel
automations may remain during comparison testing. RC7 neither calls nor requires
them.

## 2. Install the verified candidate

1. Replace `/config/custom_components/wnhf` with the packaged
   `custom_components/wnhf` directory.
2. Review `configuration/notification_targets.yaml` from this package.
3. Copy or merge it into
   `/config/wnhf/house/registry/notification_targets.yaml`.
4. Verify every installation-specific entity ID before restart, especially:
   - `tts.google_translate_de_at`
   - the five `media_player.*` Sonos entities
   - `notify.motorola_edge_40_neo`
   - `binary_sensor.wnhf_quiet_mode_active`
   - `sensor.wnhf_house_state`
5. Restart Home Assistant completely.

For a different house, change only the installation registry. Red Queen's source
must not contain that house's speaker, TTS, mobile or context entity IDs.

## 3. Post-restart preflight

Confirm that Red Queen reports:

- Red Queen `1.0.0-rc7`
- WNHF `1.33.0`
- release baseline `WP-4.7.13.2`
- runtime ready with no new Red Queen setup errors
- notification capability available

## 4. Controlled office announcement

Run a dry-run first:

```yaml
action: wnhf.execution_dry_run
data:
  action_id: notifications.announce
  target:
    object_id: announcement.target.office
  parameters:
    message: Red Queen Testdurchsage. Die lokale Sprachausgabe funktioniert.
    level: info
```

Expected: accepted dry-run, no sound and no provider call.

Then run the real action:

```yaml
action: wnhf.execution_execute
data:
  action_id: notifications.announce
  target:
    object_id: announcement.target.office
  parameters:
    message: Red Queen Testdurchsage. Die lokale Sprachausgabe funktioniert.
    level: info
```

Expected: only the Office speaker plays the message at volume `0.35`; Sonos native
announce restores previous playback and volume exactly once without a second
interruption.

## 5. Level qualification

Repeat the office action with these levels and verify spoken prefix and volume:

| Level | Prefix | Volume |
|---|---|---:|
| `info` | none | 0.35 |
| `notice` | `Hinweis.` | 0.35 |
| `warning` | `Warnung.` | 0.45 |
| `alarm` | `Achtung!` | 0.55 |

## 6. Native route qualification

Use this request and change `profile` and `priority` according to the matrix below:

```yaml
action: wnhf.execution_execute
data:
  action_id: notifications.route
  target:
    object_id: notification.route.house
  parameters:
    message: Dies ist ein kontrollierter Red Queen Routentest.
    title: Red Queen Test
    priority: warning
    profile: standard
    source: live_test
    category: system
```

| Profile | Log | Dashboard | Mobile | Voice |
|---|---:|---:|---:|---:|
| `standard` | yes | yes | yes | only when context allows |
| `silent` | yes | yes | yes | no |
| `voice` | yes | yes | no | only when context allows |
| `mobile` | yes | no | yes | no |
| `broadcast` | yes | yes | yes | yes, context override |

Dashboard creates a persistent notification only for `warning` and `critical`.
Priority maps to voice level as follows:

| Priority | Voice level |
|---|---|
| `debug` | `notice` |
| `info` | `info` |
| `warning` | `warning` |
| `critical` | `alarm` |

## 7. Guard and regression qualification

Verify that empty messages, invalid enums, unknown semantic targets and raw provider
entity IDs are rejected before dispatch. Then repeat the existing direct
`notifications.send` live test and the lighting, cover, garage and opening dry-run
regressions.

Observed results are recorded in `docs/RC7_CANDIDATE_VALIDATION.md`. Every live
acceptance item passed; RC7 may proceed to repository and GitHub web publication
preparation.
