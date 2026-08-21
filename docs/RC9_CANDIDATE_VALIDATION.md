# RC9 Candidate Validation

Candidate: Red Queen `1.0.0-rc9`
Work package: `WP-4.7.15.0` — Semantic Plant Care Core
Status: **LIVE VERIFIED**

## Static acceptance

- [x] repository verifier passes;
- [x] 67 service definitions, 8 capabilities, 22 semantic actions and 15 canonical
  real contracts;
- [x] reference `configuration/plants.yaml` contains 13 unique plant IDs;
- [x] Plant Care history uses atomic write and read-after-write verification;
- [x] `state` qualification never claims hardware verification;
- [x] RC9 normalized source checksum catalogue passes;
- [ ] hassfest and static GitHub workflows pass.

## Installation acceptance

- [x] copy `configuration/plants.yaml` to
  `/config/wnhf/house/registry/plants.yaml`;
- [x] install the RC9 integration source and restart Home Assistant;
- [x] runtime reports Red Queen `1.0.0-rc9`, WNHF `1.35.0`,
  `WP-4.7.15.0`, health 100 and no Red Queen errors/warnings;
- [x] `wnhf.plants_snapshot` returns 13 plants;
- [x] all plants start as `unknown` when no history exists;
- [x] 13 `sensor.wnhf_plant_care_*` entities are created;
- [x] 13 `button.wnhf_plant_water_*` entities are created;
- [x] every plant entity pair appears on its configured Red Queen room device and
  no plant entity remains assigned to a central Plant Care device.
- [x] `sensor.wnhf_context_engine_wnhf_context` no longer exceeds Home Assistant's
  16 KiB recorder attribute limit during startup.

## Canonical execution acceptance

- [x] dry-run of `plants.record_watering` returns `EXE-100` and sends no command;
- [x] real execution returns `EXE-000` for exactly one semantic plant;
- [x] pressing one plant button routes through `plants.record_watering`, appends
  exactly one event and refreshes the matching sensor;
- [x] result reports `verification_scope: state`, `framework_verified: true` and
  `hardware_verified: false`;
- [x] corresponding sensor changes from `unknown` to `ok`;
- [x] `last_watered_at`, `due_at`, `days_until_due` and `watering_count` are correct;
- [x] unknown plant target returns `EXE-203` without a history write;
- [x] unexpected parameters return `EXE-204` without a history write;
- [x] history and sensor state survive a full Home Assistant restart.

## Regression acceptance

- [x] inherited lighting, cover, garage, opening and notification capabilities remain
  loaded and healthy on the unchanged live-verified RC8 contracts;
- [x] final system status remains healthy with zero Red Queen errors/warnings.

## Live result

The Weidnerhome reference installation completed the controlled qualification on
2026-08-21. The office dragon-tree button recorded exactly one persistent event at
`2026-08-21T08:51:48.389787+00:00`; the plant changed from `unknown` to `ok`, its
14-day due time was calculated correctly, and the same event survived a full Home
Assistant restart without duplication. Final runtime status was healthy and ready
with health score 100, zero Red Queen errors/warnings and no active or queued
transactions.

**Red Queen 1.0.0-rc9 / WP-4.7.15.0 is LIVE VERIFIED on the reference installation
as of 2026-08-21.**
