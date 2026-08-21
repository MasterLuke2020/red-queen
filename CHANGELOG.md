# Changelog

All notable public changes to Red Queen are documented here.

## [Unreleased]

### 1.0.0-rc10 candidate — WP-4.7.16.0

#### Added

- One native room-associated opening state entity for every enabled opening.
- Native room locks, electric door-release buttons and garage cover controls.
- Explicit blade-open and blade-close buttons for capable venetian blinds.

#### Changed

- Native lights, covers, blades, locks, door release, garage and Plant Care buttons
  route through the canonical execution service and surface rejected guards as Home
  Assistant errors.
- Central health, security and aggregate diagnostics remain central by design.

#### Compatibility and safety

- No public action, service, capability or registry schema was added or renamed.
- Access controls preserve explicit confirmation and objective feedback guards.
- Blade position, latch release, physical door opening and unobserved garage
  direction remain unclaimed.

#### Validation

- Static repository and packaged-source verification passed.
- Reference-installation native room, lighting, blade, lock, door-release and garage
  tests passed on 2026-08-21.
- Restart completed with 23 rooms, valid Registry/validation, runtime ready, health
  100 and zero Red Queen errors or warnings.

### 1.0.0-rc9 candidate — WP-4.7.15.0

#### Added

- Optional semantic `plants.yaml` registry with 13 Weidnerhome reference plants.
- `plants.snapshot`, `wnhf.plants_snapshot`, one Home Assistant sensor and one
  canonical record-watering button per plant.
- Canonical `plants.record_watering` with atomic persistent watering history.
- `unknown`, `ok`, `due` and `overdue` interval/history states.

#### Safety and qualification

- No fictional initial watering timestamp is generated.
- State-scoped success proves persistence but not physical watering or soil moisture.
- Unknown targets and unexpected parameters reject before the history is changed.
- Climate control remains deliberately deferred.

### 1.0.0-rc8 candidate — WP-4.7.14.0

#### Added

- Canonical `covers.blades_open` and `covers.blades_close` using the existing
  installation-owned venetian-blind command mappings.
- Canonical `openings.release` mapped to the existing electric door-opener
  capability and semantic door objects.
- Closed-door, command-availability and explicit-confirmation guards for electric
  door release.
- Dispatch-scoped qualification metadata for blade and door-opener execution.

#### Changed

- Canonical real-execution surface now contains fourteen actions.
- Semantic action catalogue now contains twenty actions.
- Cover blade commands are no longer native-only; objective blade-position feedback
  is intentionally not required.

#### Safety and qualification

- Blade commands are blocked while a cover reports opening or closing.
- `openings.release` sends exactly one configured pulse only when the semantic door
  is available, proven closed and the request is explicitly confirmed.
- Successful blade execution does not claim blade angle or final blade state.
- Successful door release does not claim latch release or physical door opening.
- Both feature groups record framework verification at dispatch scope and remain
  `hardware_verified: false`.

#### Validation

- Static contract, syntax, semantic-action and mapping validation passed.
- Reference-installation live qualification passed on 2026-08-21.
- Blade open/close dispatch, moving-cover rejection, both confirmed electric
  door-openers, missing-confirmation rejection and open-door rejection passed.
- Final runtime health was 100 with zero Red Queen errors and warnings.

### 1.0.0-rc7 candidate — WP-4.7.13.2

#### Added

- Native canonical `notifications.announce` with four announcement levels.
- Native canonical `notifications.route` with priority/profile channel routing.
- Provider-neutral announcement targets and notification routes in the existing
  optional notification registry.
- Native Home Assistant TTS execution; Sonos targets use a TTS Media Source through
  `media_player.play_media` with `announce: true`.
- Context-guarded standard/voice routing plus explicit broadcast override.
- Per-channel log, dashboard, mobile and voice execution results.

#### Changed

- Canonical real-execution surface now contains eleven actions.
- Semantic action catalogue now contains seventeen actions.
- The historical WNHF notification/voice scripts are behavior references only and
  are no longer runtime dependencies.

#### Safety and privacy

- Raw TTS, speaker and notify entity IDs remain installation configuration and are
  rejected from the provider-neutral public request envelope.
- Invalid priority/profile/level values and empty messages reject before dispatch.
- Announcements are serialized per semantic target. Sonos owns native overlay
  ducking/restoration; Red Queen deliberately sends no second snapshot or restore
  command.
- Qualification remains dispatch-scoped and claims neither delivery/read nor audible
  playback.

#### Validation

- Static verification and isolated provider behavior validation passed.
- Reference-installation live qualification passed on 2026-08-20.
- Office and five-speaker house announcements passed for all four levels; native
  Sonos restoration resumed music exactly once without a second interruption.
- All five routing profiles, all four priority mappings, Quiet Mode suppression and
  broadcast override passed with log/dashboard/mobile/voice channel evidence.
- Request guards and lighting, cover, garage and opening dry-run regressions passed.
- Final system health: 100, runtime ready, zero Red Queen errors and zero warnings.

### 1.0.0-rc6 candidate — WP-4.7.13.1

#### Added

- Provider-neutral semantic `notifications` capability with
  `notifications.snapshot` and canonical `notifications.send`.
- Provider-owned semantic target registry at
  `/config/wnhf/house/registry/notification_targets.yaml`.
- Home Assistant notify-entity provider `provider.core.notifications`.
- Required-parameter support in canonical action contracts.
- Dispatch-scoped provider and qualification evidence semantics.

#### Changed

- Canonical real-execution surface now contains nine actions.
- Semantic action catalog now contains fifteen actions across seven capabilities.
- Notifications is now an active release-scope domain; climate and media remain
  planned.
- Execution Manager release marker advanced to `1.6-rc6`.
- Dry-run and real-execution contracts advanced to `1.7-rc6` and `1.8-rc6`.

#### Safety and privacy

- `notifications.send` requires a non-empty `message` and accepts only optional
  `title` in addition.
- Notification sends require no confirmation and are intentionally non-idempotent.
- A successful send proves Home Assistant dispatch only; it does not claim delivery
  or read receipt.
- Dispatch evidence is framework-verified but never hardware-verified.
- Persistent qualification evidence stores no notification message/title text.
- Evidence merging preserves verification flags instead of promoting dispatch-only
  evidence to hardware-verified.

#### Validation

- Live Home Assistant verification passed on 2026-08-17.
- Valid dry-run, empty-message guard, unknown-target guard and two identical real
  sends passed with the expected canonical result codes.
- Both identical notifications arrived, confirming non-idempotent execution.
- Final system health: 100, runtime ready, zero errors and zero warnings.

### 1.0.0-rc5 candidate — WP-4.7.12.1

#### Added

- First-class semantic `garage` capability with `garage.snapshot`.
- Canonical real execution for `garage.open` and `garage.close`.
- Explicit confirmation requirement for both canonical garage directions.
- Guarded residential OSC execution with objective open/closed end-position feedback.

#### Changed

- Canonical real-execution surface now contains eight actions.
- Semantic action catalog now contains thirteen actions.
- Garage is now an active release-scope domain rather than planned state-only support.

#### Safety

- Already-satisfied garage requests send no OSC pulse.
- Moving and intermediate garage states reject canonical open/close without a pulse.
- Unavailable or contradictory end-position feedback rejects execution.
- Canonical `garage.stop` and `garage.toggle` are intentionally not exposed.
- A dispatched direction succeeds only after the requested terminal end position is confirmed.

#### Validation

- Static candidate validation and isolated provider behavior tests passed.
- Live Home Assistant verification passed on the reference installation on 2026-08-16.
- Canonical garage open/close, both idempotency paths, moving-state rejection, and intermediate-position rejection were hardware-verified.

### 1.0.0-rc4 candidate — WP-4.7.11.1

#### Added

- Canonical real execution for `openings.lock`.
- Canonical real execution for `openings.unlock`.
- Explicit confirmation requirement for both canonical lock directions.
- Feedback-guarded idempotent lock execution using the existing Access object contract.
- Open-door guard preventing canonical lock commands while the door contact reports open.

#### Changed

- Canonical real-execution surface now contains six actions:
  `lighting.turn_on`, `lighting.turn_off`, `covers.open`, `covers.close`,
  `openings.lock`, and `openings.unlock`.
- Semantic action catalog now contains ten actions.

#### Verified

- Confirmation gate (`EXE-202`) and valid confirmed dry-run (`EXE-100`).
- Real unlock and lock execution with confirmed feedback (`EXE-000`).
- Already-satisfied lock/unlock idempotency with no duplicate command (`EXE-101`).
- Open-door lock rejection in dry-run and real execution without a hardware command.
- Lock and unlock execution on both configured entrance doors.
- RC3 canonical lighting and cover execution remained unchanged.

### 1.0.0-rc3 candidate — WP-4.7.10.2

#### Added

- Canonical real execution for `covers.open` and `covers.close`.
- Symmetric feedback guards for already-satisfied, already-in-progress, opposite-direction, and real-command cover paths.
- `EXE-102 already_in_progress` for duplicate movement requests.
- Optional cover Registry binding `feedback.closed_percent_entity_id`.
- Read-only native Home Assistant cover position derived from PLC closing degree.

#### Changed

- Cover `OPEN` and `CLOSED` feedback now represent true physical end positions.
- Stable `OPEN=false` and `CLOSED=false` is treated as an intermediate position.
- Automatic cover direction reversal remains blocked by canonical execution.

#### Verified

- Native cover position at open, closed, and intermediate positions.
- `covers.open`: real command, already-in-progress, and already-satisfied paths.
- `covers.close`: real command, already-in-progress, and already-satisfied paths.
- Opposite-direction guard without automatic reversal.
- RC2 canonical lighting regression remained operational.

## [1.0.0-rc2] - 2026-08-15

### Fixed

- Changed `wnhf.execution_execute` Home Assistant response support from response-only to optional response semantics so mutating canonical execution can be called directly from dashboards and ordinary automations.

### Added

- Canonical real execution for `lighting.turn_on`.
- Bidirectional feedback-guarded canonical lighting execution for `lighting.turn_on` and `lighting.turn_off`.
- Idempotent no-command behavior when the requested lighting state is already satisfied.

### Verified

- Direct dashboard canonical execution without a wrapper script.
- `lighting.turn_on`: real command path and already-satisfied path.
- `lighting.turn_off`: real command path and already-satisfied path.

## [1.0.0-rc1] - 2026-08-09

### Added

- First Red Queen release candidate.
- Semantic house/room model, provider/capability architecture, context/rules/policies/decisions.
- Canonical execution and dry-run APIs.
- Feedback-guarded `lighting.turn_off` real execution.
- Persistent execution qualification evidence and runtime diagnostics.
