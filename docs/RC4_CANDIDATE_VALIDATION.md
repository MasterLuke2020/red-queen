# Red Queen 1.0.0-rc4 Candidate Validation

## Work Package

**WP-4.7.11.1 — Canonical Door Lock / Unlock Execution**

Candidate baseline: WNHF 1.30.0  
Public candidate: Red Queen 1.0.0-rc4  
Canonical execution API: 1.0  
Canonical execution contract: 1.6-rc4

## Scope

Adds exactly two canonical mutating actions:

- `openings.lock`
- `openings.unlock`

Both target exactly one semantic `Opening` object by `target.object_id`, accept no
parameters, and require `confirmed: true`.

The existing object-level Access contract remains the technical source of truth:
`openings.lock -> access.lock` and `openings.unlock -> access.unlock`.

Door-opener and garage commands are intentionally not promoted into canonical
execution by this work package.

## Guards

Canonical lock/unlock preflight requires:

- known and enabled semantic opening object;
- configured motor-lock command for the requested direction;
- available Access runtime feedback;
- stable lock feedback (`locked` or `unlocked`);
- closed door contact;
- explicit confirmation;
- empty parameter map.

If the requested lock state is already present, the provider returns `no_action` and
sends no hardware command. A real command is successful only after the requested lock
feedback is observed.

## Expected canonical results

- dry-run without confirmation: `EXE-202` confirmation_required;
- valid confirmed dry-run: `EXE-100` dry_run_ready;
- real lock/unlock with confirmed feedback: `EXE-000`;
- repeated already-satisfied request: `EXE-101`, no command;
- open-door request: provider preflight rejects, no command;
- unavailable/invalid lock feedback: provider preflight rejects, no command;
- command sent but requested feedback not observed before timeout: `EXE-301`.

## Static validation

PASS

- Python AST parse: 95 files
- JSON parse: 4 files
- YAML parse: 18 files
- Home Assistant services: 66 unique service definitions
- Manifest domain/name/version: `wnhf` / `Red Queen` / `1.0.0-rc4`
- Semantic action catalog: 10 actions
- Canonical real-execution contracts: exactly 6
- `openings.lock` and `openings.unlock` require explicit confirmation
- No user Registry migration is required

## Isolated behavior tests

PASS

Provider tests covered:

- locked -> `openings.unlock` -> exactly one `access.unlock` command -> unlocked feedback -> success;
- repeated unlock -> no command;
- unlocked -> `openings.lock` -> exactly one `access.lock` command -> locked feedback -> success;
- open-door guard -> rejected without command;
- unavailable feedback -> rejected without command;
- feedback timeout after dispatch -> failed with command sent and feedback unconfirmed.

Planner/catalog tests covered:

- action catalog contains 10 unique semantic actions;
- canonical action contract contains exactly the six enabled actions;
- `openings.lock` / `openings.unlock` are confirmation-required;
- unconfirmed dry-run returns `EXE-202` before provider validation;
- confirmed valid dry-run returns `EXE-100`.

## Live verification status

**LIVE VERIFIED — 2026-08-15.**

Reference-installation validation passed:

- `release_info` matched RC4 / WNHF 1.30.0 / WP-4.7.11.1 / contract 1.6-rc4;
- `execution_manager` reported 10 declared/ready actions and 6 real/executable actions;
- unconfirmed `openings.unlock` dry-run correctly rejected with `EXE-202`;
- confirmed `openings.unlock` dry-run returned `EXE-100`;
- courtyard entrance real unlock returned `EXE-000`;
- repeated courtyard unlock returned `EXE-101` without a duplicate command;
- courtyard open-door guard rejected both dry-run and real `openings.lock` without a command;
- courtyard real lock returned `EXE-000`;
- repeated courtyard lock returned `EXE-101` without a duplicate command;
- street entrance real unlock returned `EXE-000`;
- street entrance real lock returned `EXE-000`.

WP-4.7.11.1 is LIVE VERIFIED. Repository CI is still required before tagging or
publishing RC4.
