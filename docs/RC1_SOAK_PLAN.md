# Red Queen 1.0.0-rc1 — Soak / Acceptance Plan

## Goal

The RC is already live-verified. The soak phase is intended to expose defects that appear only during normal home operation rather than scripted regression tests.

A practical internal target is roughly one week of normal operation, or at minimum several genuine day/night cycles with ordinary manual use, state changes and Home Assistant lifecycle events.

## Observe

### Runtime

- `wnhf.system_status` remains `healthy` with health score `100` under normal conditions.
- No new Red Queen warnings/errors appear in Home Assistant logs.
- Registry validation remains valid with quality score `100` after the system has fully started.

### State

- Light state remains stable and reflects real feedback.
- Openings remain stable and available.
- Cover state remains stable; canonical mutating cover execution is not part of RC1.
- Context and security aggregation remain plausible through ordinary daily changes.

### Lifecycle

- Normal Home Assistant restarts complete without Red Queen errors.
- Config-entry reload remains safe.
- Persistent qualification evidence survives restart/reload.

### Execution

- No unexpected real hardware commands occur.
- `lighting.turn_off` remains idempotent: feedback already OFF means no command (`EXE-101`).
- Real ON → OFF execution remains feedback-confirmed (`EXE-000`) when naturally exercised.

## Acceptance decision

### Promote to `1.0.0`

Promote when the soak phase finds no RC blocker and no runtime-functional change is required.

### Create `1.0.0-rc2`

Create another RC if a defect requires runtime code changes, changes a public contract, alters provider/execution behavior, or requires migration logic.

## Scope freeze

Do not add climate/temperature, canonical cover actuation, garage/gate execution, notifications or media during the RC1 soak phase.
