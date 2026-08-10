# WNHF Unified Provider Diagnostics API v1.0

Action:

```yaml
action: wnhf.provider_diagnostics
```

Each provider contains:

```text
identity
runtime
contract
registry
discovery
qualification
confidence
capabilities
diagnostics
```

The diagnostics API is read-only and consolidates data from:

- Provider Contract
- Provider Registry
- Provider Discovery
- Provider Runtime
- Provider Qualification
- Provider Confidence

It does not alter provider selection or execution behavior.
