# Changelog

All notable public changes to Red Queen are documented here.

## [Unreleased]

### 1.0.0 stable — WP-4.7.20.0

#### Stable promotion
- Promotes the fully qualified RC14 surface to Red Queen `1.0.0`.
- Keeps the Home Assistant domain `wnhf`.
- Keeps canonical execution API `1.0`.
- Keeps canonical real-execution contract `2.3-rc11`.
- Adds HACS publication metadata and Red Queen brand assets.

#### Qualification
- Fresh managed installation and generated dashboard: PASS.
- Exact RC14 → stable upgrade preserving `/config/wnhf`: PASS.
- Restart persistence: PASS.
- Recovery/fail-closed behavior: PASS.
- Config-entry remove/re-add: PASS.
- Real HACS clean installation: PASS.
- HACS redownload/reinstall with byte-identical `/config/wnhf`: PASS.
- Final immutable exact-package qualification remains the last release gate.

### 1.0.0-rc14 candidate — WP-4.7.20.0

#### Added
- Read-only Migration & Repair preview for manual and managed registries.
- Source-SHA guarded explicit manual → managed adoption.
- Guided repair for missing/disabled configured entity references.
- Guided repair for invalid stored Home Assistant area/floor links.

#### Changed
- Manual registries can be explicitly adopted only after eligibility preview and a
  second confirmation.
- Accepted migration/repair writes use complete candidate validation and managed
  backup/rollback transactions.
- Repair preserves semantic object IDs and fails closed when source data changes.

#### Compatibility and safety
- Canonical execution API remains 1.0.
- Canonical real-execution contract remains 2.3-rc11.
- Home Assistant registries are not mutated by guided repair.
- Physical execution guards are unchanged.

#### Validation
- WP14.1 preview qualification: PASS.
- WP14.2 manual adoption, source-SHA refusal, backup and restart persistence: PASS.
- WP14.3 entity repair, repair stale-source refusal and HA area/floor-link repair: PASS.
- Freeze source commit: `5ec86514f96f88104a3531f669ca3d58b49910cb`.
- Final frozen exact-package requalification passed with 180 integration files.
- Final package SHA-256:
  `a30b91ae143dfb089795d623b45fd26483f9dc6bad0852374b6d0f8f1bc1ad98`.


### 1.0.0-rc13 candidate — WP-4.7.19.0

#### Added
- Managed object maintenance for rooms, lights, covers, openings and plants.
- Transaction-safe enable/disable and guarded two-step deletion.
- Entity/Provider diagnostics for explicitly configured references.
- Dashboard freshness tracking against semantic registry source changes.

#### Changed
- Managed edits preserve stable semantic object IDs.
- Referenced-room and last-room deletion are blocked.
- Dashboard create/update completes without an unnecessary integration reload.

#### Compatibility and safety
- Canonical execution API remains 1.0.
- Canonical real-execution contract remains 2.3-rc11.
- Manual registries remain read-only and are never silently adopted.
- Physical execution guards are unchanged.

#### Validation
- Functional live qualification passed on 2026-09-17.
- Post-fix candidate commit: `4f35dd96ed9254ca49cc86f0d27d5ead025c24d9`.
- Post-fix 177-file candidate SHA-256:
  `bf43dcfb770f35e4fa93dba23b36a8d2667813459e93130f6cf174ed1bf1c7c5`.
- Final frozen exact-package requalification passed with 177 integration files; SHA-256 `a2d43bc3c4586d21caf7c275278980567449f0f94b75d11a4516c997f75f2b02`.


### 1.0.0-rc12 candidate — WP-4.7.18.0

#### Added
- Generated native Red Queen dashboard at `/red-queen`.
- Semantic dashboard model, unique-ID entity binding, native renderer and lifecycle adapter.
- Overview, floor views, room subviews, Plant Care and System/Diagnostics views.
- Explicit dashboard create/update controls for managed and manual registries.
- Digest-based update detection and restart persistence.

#### Changed
- Development baseline advanced to WNHF 1.38.0 / WP-4.7.18.0.
- Dashboard status presentation now distinguishes unavailable feedback from known safe/off states.
- Validator sensor attributes are compacted to avoid Recorder oversized-attribute warnings.

#### Compatibility and safety
- Canonical execution API remains 1.0.
- Canonical real-execution contract remains 2.3-rc11; RC12 does not change physical execution semantics.
- Existing manual registries remain read-only for semantic configuration.
- User/default Lovelace dashboards are not rewritten.

#### Validation
- Dashboard implementation live validation passed on 2026-08-24.
- Final exact-package qualification passed on 2026-08-24 with 174 integration files.
- Final package SHA-256: `d1c683f56990ed14aa7e488564dad67d008fbd483ec3353ca793af56fec135d7`.
- Repository static checks and Home Assistant hassfest passed after the explicit
  Lovelace dependency metadata correction.


### 1.0.0-rc11 candidate — WP-4.7.17.0

#### Added

- Managed registry ownership modes and guided Home Assistant commissioning.
- Automatic semantic IDs for configurator-created rooms and objects.
- Guided configuration for rooms, impulse lights, venetian blinds, windows,
  sliding doors, doors, garage doors and Plant Care.
- Transaction staging, backups and rollback for managed registry writes.
- Canonical guarded `garage.stop` for installations with a dedicated STOP command.
- Optional Plant Care moisture-sensor references as non-decision-driving metadata.

#### Changed

- Native venetian-blind UI remains directional; blade commands are explicit separate
  buttons and unavailable while moving.
- Garage direction controls are hidden/blocked in ambiguous intermediate state.
- Native guard failures use localized user-facing messages while retaining technical
  causes in Home Assistant logs.
- Public surface advances to 23 semantic actions, 16 canonical real-execution
  contracts and 68 Home Assistant services.

#### Compatibility and safety

- Existing manual registries remain read-only and are never silently adopted.
- Managed mutations are validated as complete bundles before replacement.
- Door access controls remain closed-door guarded.
- Cover set-position and invented blade position remain unsupported.
- Garage STOP proves dispatch only and does not claim a physical stopped position.
- Optional plant moisture input does not change RC11 watering-state decisions.

#### Validation

- Exact-package Home Assistant live qualification passed on 2026-08-22.
- Home Assistant hassfest passed on the RC11 release branch on 2026-08-23.
- Final repository static verification is required before publication.

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
