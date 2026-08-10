# WNHF Execution Plan Promotion Contract v1.0

WP-4.7.3A separates validation planning from real execution planning.

Validation plan:

```yaml
execution_enabled: false
dry_run: true
```

Promoted execution plan:

```yaml
planning_mode: execution
promoted_from_validation: true
validation_plan_id: exp_...
execution_enabled: true
dry_run: false
```

The promoted plan retains the original `request_id`, target, parameters,
selected provider IDs and provider bindings. A new `plan_id` identifies the
real execution plan.

Real provider dispatch uses the promoted plan payload, not the original
service-call arguments.
