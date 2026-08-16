# Red Queen 1.0.0-rc5 Candidate Rev2 Validation

## Work Package

**WP-4.7.12.1 — Canonical Garage Open / Close Execution**

Candidate baseline: WNHF 1.31.0
Public candidate: Red Queen 1.0.0-rc5
Canonical execution API: 1.0
Canonical dry-run contract: 1.6-rc5
Canonical real-execution contract: 1.7-rc5

## Scope

Adds a first-class semantic `garage` capability with three declared actions:

- `garage.snapshot`
- `garage.open`
- `garage.close`

Exactly two actions are promoted into canonical real execution:

- `garage.open`
- `garage.close`

Both target exactly one semantic `opening` object whose `opening_type` is
`garage_door`, accept no parameters, and require `confirmed: true`.

The existing Registry `GarageDoor` configuration remains the technical source of
truth. Residential open/stop/close (OSC) hardware is intentionally hidden behind the
semantic directional contract. No Registry migration is required.

Canonical `garage.stop` and `garage.toggle` are intentionally not exposed. A shared
OSC input is non-directional and may start movement when the actual stopped/moving
state cannot be objectively proven.

## Direction and safety contract

Canonical direction is permitted only from objective end-position feedback:

- `garage.open` + `closed` -> one OSC pulse;
- `garage.open` + `open` -> no action;
- `garage.close` + `open` -> one OSC pulse;
- `garage.close` + `closed` -> no action;
- `moving` -> reject without OSC;
- `intermediate_open` -> reject without OSC;
- unavailable feedback -> reject without OSC;
- contradictory open+closed feedback -> reject without OSC.

After a real OSC dispatch, Red Queen first observes movement start (or an immediately
reached target end state), then observes the requested terminal end position. The
terminal observation window is 60 seconds so the reference residential door's full
travel can be confirmed with margin.

## Expected canonical results

- dry-run without confirmation: `EXE-202` confirmation_required;
- valid confirmed dry-run from a stable end position: `EXE-100` dry_run_ready;
- provider-preflight rejection in dry-run (moving/intermediate/unavailable/error):
  `EXE-203`, no command;
- real request whose preflight is rejected: `EXE-206`, no command;
- real open/close with requested terminal feedback: `EXE-000`;
- repeated already-satisfied request: `EXE-101`, no command;
- command sent but movement/terminal feedback not confirmed: `EXE-301`.

## Static validation

PASS

- Python AST/compile: 95 files
- JSON parse: 4 integration files
- YAML parse: 18 integration files
- Home Assistant services: 66 unique service definitions
- Manifest domain/name/version: `wnhf` / `Red Queen` / `1.0.0-rc5`
- Semantic capability definitions: 6
- Semantic action catalog: 13 actions
- Canonical real-execution contracts: exactly 8
- `garage.open` and `garage.close` require explicit confirmation
- Garage release scope: active; active/planned domain count 16/3
- Dry-run/real/release execution version markers are coherent (`1.6-rc5` / `1.7-rc5`)
- No user Registry migration is required

## Isolated behavior validation

PASS

Provider behavior tests covered:

- closed -> `garage.open` -> exactly one OSC command -> movement -> open -> success;
- open -> `garage.close` -> exactly one OSC command -> movement -> closed -> success;
- repeated already-satisfied open -> no command;
- moving -> rejected without command;
- intermediate position -> rejected without command;
- contradictory feedback -> rejected without command;
- unavailable feedback -> rejected without command;
- movement observed but requested terminal position missing -> failed after one command;
- no movement observed after dispatch -> failed after one command.

Catalog/contract tests covered:

- 13 unique semantic actions;
- `garage.snapshot`, `garage.open`, and `garage.close` are declared;
- exactly eight canonical real-execution contracts;
- garage open/close contracts use one `target.object_id` and no parameters;
- both garage directional actions require explicit confirmation;
- unconfirmed garage dry-run returns `EXE-202` before provider validation;
- confirmed valid garage dry-run returns `EXE-100`;
- provider-preflight rejection returns `EXE-203` in dry-run.

## Candidate revision note

Rev2 corrects the dry-run response contract marker from `1.5-rc5` to the documented
`1.6-rc5` implementation version and aligns the legacy constant for the real
execution engine with `1.7-rc5`. No garage execution behavior changed.

## Live verification status

**LIVE VERIFIED — 2026-08-16**

Reference-installation results:

1. `release_info` reported Red Queen `1.0.0-rc5`, WNHF `1.31.0`,
   `WP-4.7.12.1`, canonical API `1.0`, and real-execution contract `1.7-rc5`.
2. `execution_manager` reported 6 capabilities, 13 declared/semantically-ready
   actions, and 8 canonical real/executable actions with all providers healthy.
3. Closed door, unconfirmed `garage.open` dry-run -> `EXE-202`, no command.
4. Closed door, confirmed `garage.open` dry-run -> `EXE-100`, no command.
5. Closed door, real confirmed `garage.open` -> one OSC pulse -> open terminal
   feedback -> `EXE-000`.
6. Open door, repeated `garage.open` -> `EXE-101`, no OSC pulse.
7. Open door, real confirmed `garage.close` -> one OSC pulse -> closed terminal
   feedback -> `EXE-000`.
8. Closed door, repeated `garage.close` -> `EXE-101`, no OSC pulse.
9. Moving door, canonical close request -> `EXE-206`, no command; the existing
   physical movement was not interrupted.
10. Stopped intermediate door, canonical open and close requests -> `EXE-206`,
    no command in either direction.
11. Automatic qualification persisted `real_success` and `idempotency` evidence
    for both `garage.open` and `garage.close`, hardware- and framework-verified.
12. Final post-restart system status reported `healthy`, `runtime_ready: true`,
    health score 100, zero errors and zero warnings. The empty volatile
    `last_canonical_execution` after restart is expected; persistent qualification
    evidence remained loaded and healthy.

**WP-4.7.12.1 is LIVE VERIFIED.**
