# WNHF Semantic Execution Routing Contract v1.0

The Capability Layer owns provider selection. The Generic Execution Engine routes a
promoted plan through `SemanticExecutionRouter`, which resolves the already-selected
provider and calls `provider.async_execute(...)`.

RC4 routes `lighting.turn_on`, `lighting.turn_off`, `covers.open`, `covers.close`,
`openings.lock`, and `openings.unlock` through this provider-bound canonical path.
