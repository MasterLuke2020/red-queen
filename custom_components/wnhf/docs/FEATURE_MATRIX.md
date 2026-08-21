# Red Queen 1.0.0-rc8 Candidate Feature Matrix

| Domain | Semantic model/state | Snapshot/diagnostics | Canonical execution | RC8 candidate status |
|---|---:|---:|---:|---|
| Rooms | Yes | Yes | N/A | Stable |
| Lighting | Yes | Yes | `lighting.turn_on`, `lighting.turn_off` | Live-verified baseline |
| Openings | Yes | `openings.snapshot` | `openings.lock`, `openings.unlock` | Live-verified baseline |
| Door opener | Yes | Access diagnostics / closed-door guard | `openings.release` | Live qualification pending |
| Garage | Yes | `garage.snapshot` / Access state | `garage.open`, `garage.close` | Live-verified baseline |
| Covers | Yes | `covers.snapshot`, continuous position | `covers.open`, `covers.close` | Live-verified baseline |
| Cover position | Read-only feedback | `closed_percent`, HA current position | No `SET_POSITION` | Feedback-only |
| Cover blades/slats | Native commands | No objective blade-position feedback required | `covers.blades_open`, `covers.blades_close` | Dispatch-scoped live qualification pending |
| Notifications | Yes | targets, announcement routes, channel diagnostics | `notifications.send`, `notifications.announce`, `notifications.route` | Live verified on 2026-08-20 |
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
for WP-4.7.13.2 on 2026-08-20. RC8 blade and door-release actions remain pending
reference-installation live qualification.
