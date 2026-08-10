# Qualification

## Purpose

Qualification is persistent evidence that a canonical execution path has produced hardware-significant verified outcomes. It is deliberately separate from authorization.

## Persistence

Store:

```text
/config/wnhf/qualification/execution_evidence_store.json
```

Automatic collection and persistence are enabled in RC1.

## Qualifying canonical outcomes

### EXE-000 — `real_success`

Evidence is accepted only when real execution is enabled, a command was sent, and the physical effect was confirmed through feedback.

### EXE-101 — `idempotency`

Evidence is accepted only when no command was sent and feedback confirms that the requested state was already satisfied.

Other execution result codes do not currently create canonical execution qualification evidence.

## RC1 reference evidence

At final RC1 live verification the reference installation reported:

| Evidence | Passes | Last result |
|---|---:|---|
| `auto.execution.lighting.turn_off.idempotency` | 7 | `EXE-101` |
| `auto.execution.lighting.turn_off.real_success` | 4 | `EXE-000` |
| **Total** | **11** | — |

The action/provider was both hardware-verified and framework-verified.

## Reload semantics

Config-entry reload resets volatile in-memory execution history but retains the persistent evidence store. This behavior was explicitly verified in the RC1 regression gate.

## Non-goal

Qualification is **not execution authorization**. A previously qualified action can still be rejected later because its provider is unavailable/unhealthy, its request is invalid, confirmation is missing, or live feedback does not permit safe dispatch.
