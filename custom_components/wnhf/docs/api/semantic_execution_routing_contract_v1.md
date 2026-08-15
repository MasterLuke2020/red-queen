# WNHF Semantic Execution Routing Contract v1.0

WP-4.7.4 removes direct Provider Registry access from GenericExecutionEngine.

```text
GenericExecutionEngine
→ SemanticExecutionRouter
→ selected provider from promoted execution plan
→ provider.async_execute(...)
```

The Capability Layer remains responsible for provider selection. The router
only resolves the already-selected provider ID to the provider instance and
normalizes the provider execution result.

The RC2 candidate enables `lighting.turn_on` and `lighting.turn_off` through the
same provider-bound canonical route.
