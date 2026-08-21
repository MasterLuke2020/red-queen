# Red Queen 1.0.0-rc8

## WP-4.7.14.0 — Canonical Cover Blades / Electric Door Release

RC8 promotes two already configured physical functions into provider-neutral Red
Queen execution.

- canonical `covers.blades_open`;
- canonical `covers.blades_close`;
- canonical `openings.release`;
- exactly one semantic target per request;
- no raw Home Assistant entity IDs in the public request envelope;
- no parameters for any of the three actions;
- explicit confirmation required for `openings.release`;
- closed-door and command-availability guards before door-opener dispatch;
- moving-cover and command-availability guards before blade dispatch;
- exactly one configured `button.press` per successful execution;
- dispatch-scoped qualification for effects that typical installations cannot
  objectively measure.

Objective blade-position feedback is deliberately not required. Successful blade
execution proves completion of the configured command dispatch; it does not claim a
blade angle or final blade state.

Successful `openings.release` proves completion of the configured electric
door-opener command dispatch. It does not claim that the latch released, that a
person pushed the door or that the door subsequently opened.

## Compatibility

The canonical lighting, directional cover, garage, lock/unlock and notification
contracts are unchanged. Native Home Assistant cover tilt controls remain available.
The canonical service remains `wnhf.execution_execute`; the technical integration
domain remains `wnhf`.

## Qualification status

Static repository and isolated contract verification passed.

WP-4.7.14.0 was live verified on the reference Home Assistant installation on
2026-08-21:

- Red Queen started as `1.0.0-rc8` with runtime ready, health score 100, zero
  errors and zero warnings;
- `covers.blades_open` and `covers.blades_close` returned `EXE-000` and visibly
  operated only the selected office courtyard blind blades;
- a blade request during active cover travel returned `EXE-203` without a blade
  pulse;
- an unconfirmed `openings.release` request returned `EXE-202` without a pulse;
- confirmed dry-runs for the courtyard and street doors returned `EXE-100`;
- confirmed real release for both doors returned `EXE-000`, produced exactly one
  opener pulse and allowed each door to be physically opened;
- an open-door release request returned `EXE-203` without a pulse;
- blade-open, blade-close and door-release evidence remained dispatch-scoped with
  `framework_verified: true` and `hardware_verified: false`;
- final runtime health remained 100 with no Red Queen log error or warning.

**Red Queen 1.0.0-rc8 / WP-4.7.14.0 is LIVE VERIFIED.**
