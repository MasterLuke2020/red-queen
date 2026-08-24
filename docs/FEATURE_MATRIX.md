# Red Queen 1.0.0-rc12 Candidate Feature Matrix

| Domain | Semantic/native surface | Canonical execution | RC12 candidate status |
|---|---|---|---|
| Rooms | Semantic rooms + HA room devices + generated room subviews | N/A | Live verified |
| Lighting | Native light per controllable toggle object | `lighting.turn_on`, `lighting.turn_off` | 34 controllable lights on reference registry; dashboard live verified |
| Openings | Native state per enabled opening | `openings.lock`, `openings.unlock` | Dashboard projection live verified |
| Door opener | Guarded native button | `openings.release` | Dashboard projection live verified |
| Garage | Native cover/opening state | `garage.open`, `garage.close`, `garage.stop` | Dashboard projection live verified; physical guards unchanged |
| Covers | Native directional cover + optional read-only position | `covers.open`, `covers.close` | Dashboard projection live verified |
| Cover blades | Optional explicit native buttons | `covers.blades_open`, `covers.blades_close` | Dashboard projection live verified |
| Notifications | Semantic targets/routes | `notifications.send`, `notifications.announce`, `notifications.route` | Existing live-verified surface unchanged |
| Plant Care | Native care sensor + record-watering button | `plants.record_watering` | Generated Plant Care view live verified |
| Security | Native diagnostic state | No mutating action | Generated overview/system state live verified |
| Configuration | Manual read-only or managed transaction-safe configurator | No physical execution | RC11 base retained; RC12 adds dashboard lifecycle menu |
| Generated Dashboard | Native Lovelace overview/floors/room subviews/plants/system | Uses native Red Queen entities only | Create/update/digest/restart persistence live verified |
| Dashboard dependencies | Home Assistant native cards only | N/A | No mandatory HACS/frontend dependency |
| Rules / Context / Policies / Decisions | Existing semantic engines | Compatibility/evaluation surfaces | Unchanged |
| Execution / Scheduler | Canonical Stage-4.7 path | 23 semantic actions / 16 real contracts | Contract remains `2.3-rc11` |
| Climate / temperature | Planned | Planned | Future work |
| Media | Planned | Planned | Future work |

RC12 does not move safety logic into Lovelace. The generated dashboard only invokes
native Red Queen entities/actions; canonical guards remain authoritative.
