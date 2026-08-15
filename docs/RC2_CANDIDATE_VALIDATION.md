# Red Queen WP-4.7.10.1 — RC2 Candidate Validation

## Scope

Red Queen 1.0.0-rc2 candidate addresses the RC1 dashboard response-contract bug and expands canonical lighting execution from OFF-only to bidirectional ON/OFF.

## Functional changes

- `wnhf.execution_execute` changed from Home Assistant `SupportsResponse.ONLY` to `SupportsResponse.OPTIONAL`.
- The handler returns the canonical response only when the caller requests response data; normal dashboard/automation calls may execute without a response.
- Added canonical `lighting.turn_on`.
- Retained canonical `lighting.turn_off`.
- Both actions target exactly one semantic light object via `target.object_id` and accept no parameters.
- Both use the same guarded momentary pulse with PLC feedback.
- Requested state already satisfied -> no command (`EXE-101`).
- Real state transition confirmed -> success (`EXE-000`).
- Execution capability diagnostics now expose both ON and OFF lighting capabilities.

## Compatibility

- Technical integration domain remains `wnhf`.
- Service IDs remain unchanged.
- Registry/config paths remain unchanged.
- Existing native `light.wnhf_*` and `cover.wnhf_*` entities remain unchanged.
- Existing qualification evidence store remains compatible.
- Legacy execution services remain untouched.

## Static validation completed

- Python compile/AST parse: PASS
- JSON parse: PASS
- YAML parse: PASS
- `services.yaml` inventory: 66 services
- manifest ordering: PASS
- manifest version: `1.0.0-rc2`
- canonical enabled actions: `lighting.turn_on`, `lighting.turn_off`
- `execution_execute` response mode: OPTIONAL
- `execution_dry_run` response mode: ONLY
- no `__pycache__` or `.pyc` in package

## Isolated pipeline behavior test

- OFF -> `lighting.turn_on`: one command, ON feedback confirmed — PASS
- ON -> `lighting.turn_on`: zero commands, already satisfied — PASS
- ON -> `lighting.turn_off`: one command, OFF feedback confirmed — PASS
- OFF -> `lighting.turn_off`: zero commands, already satisfied — PASS

## Required live Home Assistant validation

1. Replace `/config/custom_components/wnhf` with the candidate package and restart Home Assistant.
2. Confirm startup without Red Queen errors.
3. Confirm `wnhf.release_info` reports `1.0.0-rc2`, `rc2`, baseline `WP-4.7.10.1`.
4. Confirm `wnhf.execution_manager` reports 6 declared semantic actions and 2 real/executable canonical actions when Lighting provider is healthy.
5. Direct dashboard call to `wnhf.execution_execute` must work without a wrapper script.
6. `lighting.turn_on` with light OFF -> `EXE-000`, command sent, ON feedback confirmed.
7. Repeat `lighting.turn_on` with light ON -> `EXE-101`, no command.
8. `lighting.turn_off` with light ON -> `EXE-000`, command sent, OFF feedback confirmed.
9. Repeat `lighting.turn_off` with light OFF -> `EXE-101`, no command.
10. Test at least two additional registered lights.
11. Verify native lights/covers and existing house/openings/security/context diagnostics remain correct.
12. Confirm qualification evidence persists for both canonical actions.

## Release rule

Do not tag or publish `v1.0.0-rc2` until live validation and GitHub CI both pass.
