# Red Queen 1.0.0-rc1 Feature Matrix

| Domain | Semantic model/state | Stable snapshot/diagnostics | Canonical mutating execution | RC1 status |
|---|---:|---:|---:|---|
| Rooms | Yes | Yes | N/A | Stable |
| Lighting | Yes | Yes | `lighting.turn_off` | Stable |
| Openings | Yes | `openings.snapshot` | No | Stable state/read surface |
| Covers | Yes | `covers.snapshot` | Not yet | Stable state/read surface |
| Security | Yes | `security.snapshot` | No | Stable state/read surface |
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
| Climate / temperature | Planned | Planned | Planned | Post-1.0 feature work |
| Media | Planned | Planned | Planned | Post-1.0 feature work |
| Notifications | Planned | Planned | Planned | Post-1.0 feature work |
| Garage active actuation | State may exist via openings/security | Partial | Planned | Post-1.0 feature work |

`1.0` defines a stable foundation and a deliberately bounded feature surface; it does
not mean that every future smart-home domain or mutating action is already implemented.
