# Changelog

All notable public changes to Red Queen will be documented here.

## [Unreleased]

- RC soak phase. No new feature work is permitted in the `1.0.0-rc1` release line.

## [1.0.0-rc1] - 2026-08-09

### Added

- First public release-candidate identity under the product name **Red Queen**.
- Stable semantic house/room model and normalized state surfaces.
- Provider and capability architecture.
- Context, rules, policies and decisions.
- Canonical execution entry `wnhf.execution_execute`.
- Canonical dry-run entry `wnhf.execution_dry_run`.
- Feedback-guarded `lighting.turn_off` real execution.
- Persistent execution qualification evidence.
- Runtime health, validation, release metadata and public API diagnostics.

### Verified

- Runtime health `100` and registry quality `100`.
- Public API classification `66/66` with no duplicates.
- `EXE-101` idempotency path with no command sent when state is already satisfied.
- `EXE-000` real hardware path with feedback confirmation.
- Config-entry reload and qualification persistence.

### Compatibility

- Home Assistant domain remains `wnhf`.
- Existing `wnhf.*` services and persisted `/config/wnhf` data remain intentionally compatible with the verified WNHF development baseline.
