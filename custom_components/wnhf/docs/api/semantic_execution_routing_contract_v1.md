# WNHF Semantic Execution Routing Contract v1.0

The Capability Layer owns provider selection. The Generic Execution Engine routes a
promoted plan through `SemanticExecutionRouter`, which resolves the already-selected
provider and calls `provider.async_execute(...)`.

RC8 routes `lighting.turn_on`, `lighting.turn_off`, `covers.open`,
`covers.close`, `covers.blades_open`, `covers.blades_close`, `garage.open`,
`garage.close`, `openings.lock`, `openings.unlock`, `openings.release`,
`notifications.send`, `notifications.announce` and
`notifications.route` through this provider-bound canonical path. Notification
channel fan-out occurs inside the selected notification provider and never changes
the Capability Layer's exactly-one-provider rule.
