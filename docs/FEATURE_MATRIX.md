# Red Queen 1.0.0-rc9 Candidate Feature Matrix

| Domain | Semantic model/state | Stable snapshot/diagnostics | Canonical mutating execution | RC9 candidate status |
|---|---:|---:|---:|---|
| Rooms | Yes | Yes | N/A | Stable |
| Lighting | Yes | Yes | `lighting.turn_on`, `lighting.turn_off` | Live-verified baseline |
| Openings | Yes | `openings.snapshot` | `openings.lock`, `openings.unlock`, `openings.release` | Door release live verified in RC8 |
| Covers | Yes | `covers.snapshot`, continuous position feedback | `covers.open`, `covers.close`, `covers.blades_open`, `covers.blades_close` | Blades live verified in RC8 |
| Garage | Yes | `garage.snapshot` / Access state | `garage.open`, `garage.close` | Live-verified baseline |
| Notifications | Yes | direct, announcement and route diagnostics | `notifications.send`, `notifications.announce`, `notifications.route` | Live verified on 2026-08-20 |
| Plant Care | Yes, optional registry and persistent history | `plants.snapshot`, `wnhf.plants_snapshot`, per-plant sensors and record-watering buttons | `plants.record_watering` | State-scoped live verified on 2026-08-21 |
| Security | Yes | `security.snapshot` | No | Stable read surface |
| Providers | Yes | Yes | N/A | Stable core architecture |
| Capabilities | Yes | Yes | N/A | Stable core architecture |
| Qualification | Yes | Yes | N/A | Stable core architecture |
| Validation | Yes | Yes | N/A | Stable core architecture |
| Rules | Yes | Yes | N/A | Stable evaluation |
| Context | Yes | Yes | N/A | Stable evaluation |
| Policies | Yes | Yes | Legacy mutating routes compatibility-only | Stable evaluation |
| Decisions | Yes | Yes | Decision-ID execution is legacy | Stable evaluation |
| Execution | Yes | Yes | Canonical Stage-4.7 semantic path | Stable |
| Scheduler | Yes | Yes | Legacy compatibility support | Stable diagnostics |
| Climate / temperature | Planned | Planned | Planned | Future feature work |
| Media | Planned | Planned | Planned | Future feature work |

All notification actions are provider-neutral, require a non-empty message, need no
confirmation and are deliberately non-idempotent. Announcement targets keep raw TTS
and media-player IDs out of the public action envelope. Route targets select log,
dashboard, mobile and voice channels through priority/profile policy. Success remains
dispatch-scoped; delivery, read and audible playback are not claimed.

Blade and electric door-opener success are dispatch-scoped and deliberately do not
claim unobservable hardware state. Garage stop/toggle and cover set-position remain
outside the canonical surface.

Plant Care starts without invented history: a plant is `unknown` until a real
watering event is recorded. Thereafter interval/history state is `ok`, `due` or
`overdue`. RC9 state-scoped success proves the persistent event, not physical
watering or soil moisture.
