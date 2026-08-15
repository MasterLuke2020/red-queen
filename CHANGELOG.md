# Changelog

All notable public changes to Red Queen are documented here.

## [Unreleased]

### 1.0.0-rc2 candidate — WP-4.7.10.1

#### Fixed

- Changed `wnhf.execution_execute` Home Assistant response support from response-only to optional response semantics so mutating canonical execution can be called directly from dashboards and ordinary automations.

#### Added

- Canonical real execution for `lighting.turn_on`.
- Bidirectional feedback-guarded canonical lighting execution for `lighting.turn_on` and `lighting.turn_off`.
- Idempotent no-command behavior when the requested lighting state is already satisfied.

#### Verified

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
