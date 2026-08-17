# Red Queen 1.0.0-rc6 Feature Matrix

| Domain | Semantic model/state | Stable snapshot/diagnostics | Canonical mutating execution | RC6 status |
|---|---:|---:|---:|---|
| Rooms | Yes | Yes | N/A | Stable |
| Lighting | Yes | Yes | `lighting.turn_on`, `lighting.turn_off` | Live-verified baseline |
| Openings | Yes | `openings.snapshot` | `openings.lock`, `openings.unlock` | Live-verified baseline |
| Covers | Yes | `covers.snapshot`, continuous position feedback | `covers.open`, `covers.close` | Live-verified baseline |
| Garage | Yes | `garage.snapshot` / Access state | `garage.open`, `garage.close` | Live-verified baseline |
| Notifications | Yes | `notifications.snapshot`, provider diagnostics | `notifications.send` | LIVE VERIFIED RC6 |
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

`notifications.send` is provider-neutral, requires a non-empty message, needs no
confirmation and is deliberately non-idempotent. Its success scope is dispatch:
framework completion is verified, but remote delivery/read and hardware verification
are not claimed.

Garage stop/toggle, cover set-position/blade execution and electric door-opener
execution remain outside the canonical surface.
