# Red Queen 1.0.0-rc2

## Second release candidate

RC2 addresses the first real-world dashboard integration issue found during RC1
soak testing and expands canonical lighting execution to both target states.

### Changes

- `wnhf.execution_execute` now uses optional Home Assistant response semantics.
  Dashboard and automation callers can execute it without requesting response data;
  callers that request a response still receive the complete canonical result.
- Added canonical `lighting.turn_on`.
- Retained canonical `lighting.turn_off`.
- Both lighting actions target exactly one semantic `object_id`.
- Both actions use the same feedback-guarded momentary pulse strategy.
- If the requested target state is already satisfied, no hardware command is sent.
- Real commands require feedback confirmation of the requested ON/OFF state.
- Qualification evidence remains collected under the existing EXE-000 and EXE-101
  result contracts.

### Compatibility

The Home Assistant integration domain remains `wnhf`. Existing configuration,
entity IDs, legacy services and persisted qualification evidence remain compatible.

### Validation status

This package is an RC2 candidate and must pass static checks, Home Assistant startup,
dry-run validation, real ON/OFF execution, idempotency and regression checks before
the `v1.0.0-rc2` tag is published.
