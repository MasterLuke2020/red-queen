# Red Queen 1.0.0-rc5 Feature Matrix

| Domain | Semantic model/state | Stable snapshot/diagnostics | Canonical mutating execution | RC5 status |
|---|---:|---:|---:|---|
| Rooms | Yes | Yes | N/A | Stable |
| Lighting | Yes | Yes | `lighting.turn_on`, `lighting.turn_off` | Live-verified baseline |
| Openings | Yes | `openings.snapshot` | `openings.lock`, `openings.unlock` | Live-verified RC4 baseline |
| Door opener | Yes | Access diagnostics | Not canonical | Existing compatibility path only |
| Garage | Yes | `garage.snapshot` / Access state | `garage.open`, `garage.close` | RC5 candidate |
| Covers | Yes | `covers.snapshot`, continuous position feedback | `covers.open`, `covers.close` | Live-verified RC3 baseline |
| Cover position | Read-only feedback | `closed_percent`, HA current position | No `SET_POSITION` | Feedback-only |
| Cover blades/slats | Native commands | No objective blade-position feedback | Not canonical | Native-only until feedback exists |
| Security | Yes | `security.snapshot` | No | Stable state/read surface |
| Providers | Yes | Yes | N/A | Stable core architecture |
| Capabilities | Yes | Yes | N/A | Stable core architecture |
| Qualification | Yes | Yes | N/A | Stable core architecture |
| Validation | Yes | Yes | N/A | Stable core architecture |
| Rules / Context / Policies / Decisions | Yes | Yes | Legacy mutating routes compatibility-only | Stable evaluation |
| Execution | Yes | Yes | Canonical Stage-4.7 semantic path | Stable architecture |
| Climate / media / notifications | Planned | Planned/partial | Planned | Future feature work |

Garage direction is canonical only when objective end-position feedback proves a
stable start state. Shared OSC stop/toggle behavior remains technical and is not
exposed as a canonical action.
