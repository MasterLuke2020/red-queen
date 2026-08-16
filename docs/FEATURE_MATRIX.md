# Red Queen 1.0.0-rc5 Feature Matrix

| Domain | Semantic model/state | Stable snapshot/diagnostics | Canonical mutating execution | RC5 status |
|---|---:|---:|---:|---|
| Rooms | Yes | Yes | N/A | Stable |
| Lighting | Yes | Yes | `lighting.turn_on`, `lighting.turn_off` | Stable |
| Openings | Yes | `openings.snapshot` | `openings.lock`, `openings.unlock` | Stable |
| Covers | Yes | `covers.snapshot` | `covers.open`, `covers.close` | Stable |
| Garage | Yes | `garage.snapshot` / Access runtime | `garage.open`, `garage.close` | RC5 candidate |
| Security | Yes | `security.snapshot` | No | Stable read surface |
| Providers | Yes | Yes | N/A | Stable core architecture |
| Capabilities | Yes | Yes | N/A | Stable core architecture |
| Qualification | Yes | Yes | N/A | Stable core architecture |
| Validation | Yes | Yes | N/A | Stable core architecture |
| Rules | Yes | Yes | N/A | Stable core architecture |
| Context | Yes | Yes | N/A | Stable core architecture |
| Policies | Yes | Yes | Legacy mutating routes are compatibility-only | Stable evaluation |
| Decisions | Yes | Yes | Decision-ID execution is legacy | Stable evaluation |
| Execution | Yes | Yes | Canonical Stage-4.7 semantic path | Stable |
| Scheduler | Yes | Yes | Legacy compatibility execution support | Stable diagnostics |
| Climate / temperature | Planned | Planned | Planned | Future feature work |
| Media | Planned | Planned | Planned | Future feature work |
| Notifications | Planned | Planned | Planned | Future feature work |

`garage.stop` and `garage.toggle` are intentionally absent from the canonical surface.
Typical residential OSC hardware is non-directional; Red Queen exposes only semantic
open/close requests that can be proven safe from objective end-position feedback.
