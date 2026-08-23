# Red Queen 1.0.0-rc11 Candidate Feature Matrix

| Domain | Semantic model/state | Native room surface | Canonical execution | RC11 candidate status |
|---|---:|---:|---:|---|
| Rooms | Yes | Yes | N/A | Managed configurator live qualified |
| Lighting | Yes | Native light per controllable object | `lighting.turn_on`, `lighting.turn_off` | Execution RC10 live verified; RC11 configuration live qualified |
| Openings | Yes | Native state per enabled window/door/sliding door | `openings.lock`, `openings.unlock` | RC11 configuration and guards live qualified |
| Door opener | Yes | Native guarded button | `openings.release` | RC11 configuration and closed-door guard live qualified |
| Garage | Yes | Native cover plus opening state | `garage.open`, `garage.close`, `garage.stop` | RC11 open/close/STOP and intermediate-state guards live qualified |
| Covers | Yes | Native directional cover | `covers.open`, `covers.close` | RC11 configuration, movement and UI guards live qualified |
| Cover position | Read-only objective feedback | Dedicated `%` sensor plus HA current position | No `SET_POSITION` | RC11 live qualified |
| Cover blades/slats | Optional separate native buttons | No objective blade-position feedback required | `covers.blades_open`, `covers.blades_close` | RC11 optional configuration and moving guard live qualified |
| Notifications | Yes | targets, announcement routes, channel diagnostics | `notifications.send`, `notifications.announce`, `notifications.route` | Live verified on 2026-08-20 |
| Plant Care | Optional registry and persistent history | One care sensor and one record-watering button per plant | `plants.record_watering` | RC11 managed configuration and persistence live qualified |
| Plant moisture input | Optional configured `sensor.*` reference | Diagnostic metadata only | No moisture-driven watering action | Stored/observable; intentionally not decision-driving in RC11 |
| Security | Yes | `security.snapshot` | No | Stable read surface |
| Providers / Capabilities | Yes | Yes | N/A | Stable core architecture |
| Qualification / Validation | Yes | Yes | N/A | Stable core architecture |
| Configuration | Manual read-only or managed transaction | Guided rooms/lights/covers/openings/plants | No physical execution | RC11 reference-installation live qualified |
| Rules / Context / Policies / Decisions | Yes | Yes | Legacy mutating routes compatibility-only | Stable evaluation |
| Execution / Scheduler | Yes | Yes | Canonical Stage-4.7 path / legacy scheduling | 23 semantic actions, 16 canonical real actions |
| Climate / temperature | Planned | Planned | Planned | Future feature work |
| Media | Planned | Planned | Planned | Future feature work |

Notification success is dispatch-scoped: framework verification is recorded, while
remote delivery/read, audible playback and hardware verification are not claimed.
Native TTS, Sonos restoration and context-aware channel routing were live verified
for WP-4.7.13.2 on 2026-08-20.

RC11 does not advertise arbitrary cover positioning or blade position. Garage STOP
proves only the dedicated STOP command dispatch and does not infer the physical
stopped position. Plant Care verifies persistent watering history only; an optional
moisture sensor can be recorded in the semantic registry but does not change the
care state in RC11.
