# Canonical Execution Result Codes

The following codes are present in the RC1 canonical generic planning/real-execution contracts.

| Code | Key | Meaning |
|---|---|---|
| `EXE-000` | `succeeded` | Real execution succeeded; command/effect path completed. |
| `EXE-100` | `dry_run_ready` | Dry-run request is valid and a non-dispatching plan was built. |
| `EXE-101` | `already_satisfied` | Feedback already satisfies requested state; no command is sent. |
| `EXE-200` | `action_not_found` | Semantic action is not declared. |
| `EXE-201` | `action_not_ready` | Semantic action is not currently ready / not enabled for requested path. |
| `EXE-202` | `confirmation_required` | Required explicit confirmation is absent. |
| `EXE-203` | `invalid_target` | Canonical target contract or semantic/provider target validation failed. |
| `EXE-204` | `invalid_parameters` | Parameters violate the canonical action contract. |
| `EXE-205` | `action_not_implemented` | Action is not implemented by the canonical real executor. |
| `EXE-206` | `plan_rejected` | Execution plan could not be accepted/promoted. |
| `EXE-207` | `provider_not_found` | Selected provider could not be found at dispatch time. |
| `EXE-208` | `provider_rejected` | Provider reported unsupported/rejected execution. |
| `EXE-300` | `command_failed` | Command/effect path failed without a more specific confirmed-effect result. |
| `EXE-301` | `effect_not_confirmed` | A command was sent but required physical feedback was not confirmed. |
| `EXE-900` | `executor_exception` | Unhandled exception was converted into a stable execution failure result. |

## Qualification significance

Only `EXE-000` and `EXE-101` currently create canonical persistent execution evidence, and only when their command/feedback invariants are satisfied.
