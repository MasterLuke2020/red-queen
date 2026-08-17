# WNHF Semantic Execution Routing Contract v1.0

The Capability Layer owns provider selection. The Generic Execution Engine routes a
promoted plan through `SemanticExecutionRouter`, which resolves the already-selected
provider and calls `provider.async_execute(...)`.

RC6 routes `lighting.turn_on`, `lighting.turn_off`, `covers.open`,
`covers.close`, `garage.open`, `garage.close`, `openings.lock`,
`openings.unlock` and `notifications.send` through this provider-bound canonical
path.
