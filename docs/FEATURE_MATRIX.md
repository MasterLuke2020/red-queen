# Red Queen 1.0.0-rc10 Candidate Feature Matrix

| Domain | Semantic model/state | Native room surface | Canonical mutating execution | RC10 candidate status |
|---|---:|---:|---:|---|
| Rooms | Yes | Yes | N/A | Stable |
| Lighting | Yes | Native light per controllable object | `lighting.turn_on`, `lighting.turn_off` | Canonical native adapter added |
| Openings | Yes | Native state per enabled window/door | `openings.lock`, `openings.unlock`, `openings.release` | Room completeness added |
| Covers | Yes | Native cover plus explicit blade buttons | `covers.open`, `covers.close`, `covers.blades_open`, `covers.blades_close` | Canonical native adapters added |
| Garage | Yes | Native garage cover plus opening state | `garage.open`, `garage.close` | Room completeness added |
| Notifications | Yes | direct, announcement and route diagnostics | `notifications.send`, `notifications.announce`, `notifications.route` | Live verified on 2026-08-20 |
| Plant Care | Yes, optional registry and persistent history | `plants.snapshot`, per-plant sensor and watering button | `plants.record_watering` | Live-verified RC9 baseline |
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
`overdue`. Plant Care state-scoped success proves the persistent event, not physical
watering or soil moisture.

Native room controls are adapters, not alternate provider paths: each productive
press or Home Assistant entity service call enters `wnhf.execution_execute`. Central
health, security and aggregate entities deliberately remain on central module devices.
