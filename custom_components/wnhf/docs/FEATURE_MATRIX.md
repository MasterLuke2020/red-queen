# Red Queen 1.0.0-rc10 Candidate Feature Matrix

| Domain | Semantic model/state | Native room surface | Canonical execution | RC10 candidate status |
|---|---:|---:|---:|---|
| Rooms | Yes | Yes | N/A | Stable |
| Lighting | Yes | Native light per controllable object | `lighting.turn_on`, `lighting.turn_off` | RC10 live verified |
| Openings | Yes | Native state per enabled window/door | `openings.lock`, `openings.unlock` | RC10 live verified |
| Door opener | Yes | Native confirmed button | `openings.release` | RC10 live verified |
| Garage | Yes | Native cover plus opening state | `garage.open`, `garage.close` | RC10 live verified |
| Covers | Yes | Native cover | `covers.open`, `covers.close` | RC10 live verified |
| Cover position | Read-only feedback | `closed_percent`, HA current position | No `SET_POSITION` | Feedback-only |
| Cover blades/slats | Native tilt plus explicit buttons | No objective blade-position feedback required | `covers.blades_open`, `covers.blades_close` | RC10 live verified |
| Notifications | Yes | targets, announcement routes, channel diagnostics | `notifications.send`, `notifications.announce`, `notifications.route` | Live verified on 2026-08-20 |
| Plant Care | Optional registry and persistent history | `plants.snapshot`, `plants_snapshot`, one sensor and record-watering button per plant | `plants.record_watering` | State-scoped live verified on 2026-08-21 |
| Security | Yes | `security.snapshot` | No | Stable read surface |
| Providers / Capabilities | Yes | Yes | N/A | Stable core architecture |
| Qualification / Validation | Yes | Yes | N/A | Stable core architecture |
| Rules / Context / Policies / Decisions | Yes | Yes | Legacy mutating routes compatibility-only | Stable evaluation |
| Execution / Scheduler | Yes | Yes | Canonical Stage-4.7 path / legacy scheduling | Stable |
| Climate / temperature | Planned | Planned | Planned | Future feature work |
| Media | Planned | Planned | Planned | Future feature work |

Notification success is dispatch-scoped: framework verification is recorded, while
remote delivery/read, audible playback and hardware verification are not claimed.
Native TTS, Sonos restoration and context-aware channel routing were live verified
for WP-4.7.13.2 on 2026-08-20. RC8 blade and door-release actions were live verified
on 2026-08-21. Plant Care does not claim objective soil moisture or physical
watering; only its persistent history mutation is verified.
