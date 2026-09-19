# Red Queen 1.0.0-rc14 Candidate Feature Matrix

| Domain | Semantic/native surface | Canonical execution | RC14 candidate status |
|---|---|---|---|
| Rooms | Semantic rooms + HA room devices + room subviews | N/A | Managed maintenance + HA-link repair live verified |
| Lighting | Native light per controllable toggle object | `lighting.turn_on`, `lighting.turn_off` | Managed maintenance + entity repair live verified |
| Openings | Native state per enabled opening | `openings.lock`, `openings.unlock` | Managed maintenance + diagnostics |
| Door opener | Guarded native button | `openings.release` | Physical guards unchanged |
| Garage | Native cover/opening state | `garage.open`, `garage.close`, `garage.stop` | Managed maintenance; guards unchanged |
| Covers | Native directional cover + optional read-only position | `covers.open`, `covers.close` | Managed maintenance |
| Cover blades | Optional explicit native buttons | `covers.blades_open`, `covers.blades_close` | Existing guarded behavior unchanged |
| Notifications | Semantic targets/routes | `notifications.send`, `notifications.announce`, `notifications.route` | Existing surface unchanged |
| Plant Care | Native care sensor + record-watering button | `plants.record_watering` | Managed maintenance |
| Configuration | Manual read-only or managed transaction-safe configurator | No physical execution | Migration/adoption/repair live verified |
| Migration preview | Source-SHA + structural/entity/HA-link analysis | N/A | Read-only behavior live verified |
| Manual adoption | Explicit manual → managed transaction | N/A | SHA refusal + backup + restart live verified |
| Guided repair | Entity refs + HA area/floor source links | N/A | Backup + stale-source refusal live verified |
| Entity/Provider diagnostics | Explicit configured references only | N/A | Production diagnostics retained |
| Generated Dashboard | Native Lovelace overview/floors/rooms/plants/system | Native Red Queen entities only | Existing source freshness/update retained |
| Dashboard dependencies | Home Assistant native cards only | N/A | No mandatory HACS/frontend dependency |
| Rules / Context / Policies / Decisions | Existing semantic engines | Compatibility/evaluation surfaces | Unchanged |
| Execution / Scheduler | Canonical Stage-4.7 path | 23 semantic actions / 16 real contracts | Contract remains `2.3-rc11` |
| Climate / temperature | Planned | Planned | Deferred beyond 1.0 |
| Media | Planned | Planned | Deferred beyond 1.0 |

RC14 does not move physical safety logic into Configuration or Lovelace. Physical
guards remain authoritative inside canonical Red Queen execution.
