# Red Queen 1.0.0-rc13 Candidate Feature Matrix

| Domain | Semantic/native surface | Canonical execution | RC13 candidate status |
|---|---|---|---|
| Rooms | Semantic rooms + HA room devices + room subviews | N/A | Managed maintenance live verified |
| Lighting | Native light per controllable toggle object | `lighting.turn_on`, `lighting.turn_off` | Managed maintenance live verified |
| Openings | Native state per enabled opening | `openings.lock`, `openings.unlock` | Managed maintenance + diagnostics live verified |
| Door opener | Guarded native button | `openings.release` | Physical guards unchanged |
| Garage | Native cover/opening state | `garage.open`, `garage.close`, `garage.stop` | Managed maintenance; guards unchanged |
| Covers | Native directional cover + optional read-only position | `covers.open`, `covers.close` | Managed maintenance live verified |
| Cover blades | Optional explicit native buttons | `covers.blades_open`, `covers.blades_close` | Existing guarded behavior unchanged |
| Notifications | Semantic targets/routes | `notifications.send`, `notifications.announce`, `notifications.route` | Existing surface unchanged |
| Plant Care | Native care sensor + record-watering button | `plants.record_watering` | Managed maintenance live verified |
| Configuration | Manual read-only or managed transaction-safe configurator | No physical execution | RC13 create/edit/enable/delete live verified |
| Entity/Provider diagnostics | Explicit configured references only | N/A | 21/21 ready, 0 findings in live test |
| Generated Dashboard | Native Lovelace overview/floors/rooms/plants/system | Native Red Queen entities only | Source freshness + update + restart live verified |
| Dashboard dependencies | Home Assistant native cards only | N/A | No mandatory HACS/frontend dependency |
| Rules / Context / Policies / Decisions | Existing semantic engines | Compatibility/evaluation surfaces | Unchanged |
| Execution / Scheduler | Canonical Stage-4.7 path | 23 semantic actions / 16 real contracts | Contract remains `2.3-rc11` |
| Climate / temperature | Planned | Planned | Deferred beyond 1.0 |
| Media | Planned | Planned | Deferred beyond 1.0 |

RC13 does not move safety logic into Configuration or Lovelace. Physical guards remain
authoritative inside canonical Red Queen execution.
