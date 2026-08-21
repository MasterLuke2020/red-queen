# RC10 Candidate Validation — WP-4.7.16.0

Status: **LIVE VERIFIED — 2026-08-21**

## Static acceptance

- [x] `python tools/verify_repository.py` passes.
- [x] Python syntax and JSON/YAML parsing pass.
- [x] LF-normalized `checksums/rc10_source.sha256` covers every integration file.
- [x] 67 services, 8 capabilities, 22 actions and 15 real contracts remain stable.
- [x] Native controls use the canonical response-aware execution bridge.

## Reference entity inventory

- [x] 21 room-associated opening binary sensors.
- [x] 2 room-associated native lock entities.
- [x] 2 room-associated confirmed door-release buttons.
- [x] 34 room-associated explicit blade buttons.
- [x] 1 room-associated native garage cover.
- [x] Existing lights, covers, Plant Care entities and central diagnostics remain.

## Live behavior

- [x] Representative opening sensors report objective closed/open state.
- [x] Lock state follows feedback and lock/unlock dispatches one guarded command.
- [x] Closed-door release dispatches one command; open-door guard remains active.
- [x] Stationary native blade buttons dispatch through canonical execution.
- [x] Garage open/close works from proven opposite end positions.
- [x] Native light and cover controls create canonical execution evidence.
- [x] Published RC9 Plant Care and notification contracts remain loaded and healthy.

## Restart and final health

- [x] Entity IDs, device links and corrected room associations survive restart.
- [x] Published RC9 Plant Care persistence remains loaded with 13 plants.
- [x] `runtime_ready: true` and `health_score: 100`.
- [x] Zero Red Queen errors and zero Red Queen warnings.

## Observed evidence

Observed final `wnhf.system_status` at `2026-08-21T10:26:00.233885+00:00`:

- framework `1.0.0-rc10`, status `healthy`, runtime ready;
- 23 rooms, 43 lights, 40 enabled lights, 38 controllable lights;
- 17 covers, 21 openings and 13 plants;
- Registry valid, validation valid, quality/health score 100;
- 5 Decisions and 5 Policies loaded;
- zero active/queued transactions;
- zero errors, zero warnings and zero out-of-scope diagnostics;
- Climate and Media remain planned and outside the RC10 scope.

The generic Home Assistant custom-integration warning and unreachable Tapo camera
errors are unrelated to Red Queen and are not counted as RC10 diagnostics. No final
blade position, latch release, physical opening or unobserved garage direction is
inferred from dispatch-scoped success.
