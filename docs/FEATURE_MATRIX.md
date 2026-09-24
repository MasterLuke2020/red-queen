# Red Queen 1.0.0 Stable Feature Matrix

| Domain | Semantic/native surface | Canonical execution | Stable 1.0 status |
|---|---|---|---|
| Rooms | Semantic rooms + HA room devices + room subviews | N/A | Supported |
| Lighting | Native light per controllable toggle object | `lighting.turn_on`, `lighting.turn_off` | Supported |
| Openings | Native state per enabled opening | `openings.lock`, `openings.unlock` | Supported |
| Door opener | Guarded native button | `openings.release` | Supported |
| Garage | Native cover/opening state | `garage.open`, `garage.close`, `garage.stop` | Supported |
| Covers | Native directional cover + optional read-only position | `covers.open`, `covers.close` | Supported |
| Cover blades | Optional explicit native buttons | `covers.blades_open`, `covers.blades_close` | Supported |
| Notifications | Semantic targets/routes | `notifications.send`, `notifications.announce`, `notifications.route` | Supported |
| Plant Care | Native care sensor + record-watering button | `plants.record_watering` | Supported |
| Configuration | Manual read-only or managed transaction-safe configurator | No physical execution | LIVE VERIFIED |
| Migration preview | Source-SHA + structural/entity/HA-link analysis | N/A | LIVE VERIFIED |
| Manual adoption | Explicit manual → managed transaction | N/A | LIVE VERIFIED |
| Guided repair | Entity refs + HA area/floor source links | N/A | LIVE VERIFIED |
| Entity/Provider diagnostics | Explicit configured references only | N/A | Supported |
| Generated Dashboard | Native Lovelace overview/floors/rooms/plants/system | Native Red Queen entities only | LIVE VERIFIED |
| Dashboard dependencies | Home Assistant native cards only | N/A | No mandatory frontend dependency |
| HACS installation | Repository installation/redownload | N/A | LIVE VERIFIED |
| Rules / Context / Policies / Decisions | Existing semantic engines | Compatibility/evaluation surfaces | Supported |
| Execution / Scheduler | Canonical Stage-4.7 path | 23 semantic actions / 16 real contracts | Contract `2.3-rc11` |
| Climate / temperature | Planned | Planned | Deferred beyond 1.0 |
| Media | Planned | Planned | Deferred beyond 1.0 |

Red Queen 1.0 keeps physical safety logic out of Configuration and Lovelace. Physical
guards remain authoritative inside canonical Red Queen execution.
