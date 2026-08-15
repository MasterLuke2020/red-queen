# Changelog

All notable public changes to Red Queen are documented here.

## [Unreleased]

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
