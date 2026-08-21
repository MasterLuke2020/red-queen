# Red Queen 1.0.0-rc9

## WP-4.7.15.0 — Semantic Plant Care Core

RC9 adds a sensor-independent Plant Care domain for installations that know their
plants and care intervals but have no objective soil-moisture feedback.

- optional installation-owned `plants.yaml` registry;
- stable semantic plant IDs, species, rooms, locations and watering intervals;
- `plants.snapshot` read contract and `wnhf.plants_snapshot` response service;
- canonical `plants.record_watering` for exactly one semantic plant;
- atomic persistent history at
  `/config/wnhf/plant_care/watering_history.json`;
- one dashboard-ready Home Assistant status sensor and one native record-watering
  button per enabled plant;
- plant sensors and buttons are attached to their existing Red Queen room device;
- button presses route through the public canonical execution surface rather than
  writing history directly;
- explicit `unknown`, `ok`, `due` and `overdue` states;
- no invented initial watering timestamps;
- state-scoped qualification with no claim that physical watering or soil moisture
  was independently observed.
- bounded native Context sensor attributes; the complete diagnostic payload remains
  available from `wnhf.context_snapshot` without overflowing Recorder attributes.

The Weidnerhome reference registry contains 13 plants: one dragon tree, three areca
palms, one sago palm, four yuccas and four ivy plants. All are intentionally
sensor-independent in RC9.

Existing lighting, cover, garage, lock/unlock, door-opener and notification contracts
remain unchanged. Climate control remains deferred.

## Qualification status

Static repository and isolated contract verification passed. Reference-installation
live qualification passed on 2026-08-21 with 13 loaded plants, correct initial
`unknown` states, one state-qualified dragon-tree watering event, immediate sensor
refresh, invalid-target and invalid-parameter rejection without history writes,
restart persistence and final health 100 with no Red Queen errors or warnings.
