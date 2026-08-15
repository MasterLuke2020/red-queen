# Red Queen 1.0.0-rc4 Feature Matrix

| Domain | Semantic model/state | Stable snapshot/diagnostics | Canonical mutating execution | RC4 status |
|---|---:|---:|---:|---|
| Rooms | Yes | Yes | N/A | Stable |
| Lighting | Yes | Yes | `lighting.turn_on`, `lighting.turn_off` | Live-verified RC2 baseline |
| Openings | Yes | `openings.snapshot` | `openings.lock`, `openings.unlock` | RC4 candidate |
| Door opener | Yes | Access diagnostics | Not canonical | Existing compatibility path only |
| Garage door | Yes | Access state/diagnostics | Not canonical | Existing compatibility path only |
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
| Climate / media / notifications | Planned | Planned/partial | Planned | Post-1.0 feature work |

Canonical execution is promoted only when Red Queen has enough objective feedback to
guard the hardware action and evaluate its effect. Lock/unlock additionally requires
explicit caller confirmation and a closed door contact before command dispatch.
