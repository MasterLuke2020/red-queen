# WNHF Capability Resolver API v1.0

Action:

```yaml
action: wnhf.capability_resolver
```

Resolution path:

```text
semantic capability
→ capability definition
→ required provider capabilities
→ provider registry
→ selected providers
→ provider runtime health
```

Public resolution states:

```text
resolved
not_found
disabled
provider_unresolved
provider_unavailable
provider_unhealthy
```

The resolver itself remains read-only and never dispatches hardware commands.
In the current cumulative baseline its output is consumed by the Capability
Manager and the canonical Stage-4.7 semantic execution planner.
