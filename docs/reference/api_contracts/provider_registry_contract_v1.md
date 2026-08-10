# WNHF Provider Registry API v1.0

Diagnostic action:

```yaml
action: wnhf.provider_registry
```

Registry indexes:

```text
provider_id → provider
capability_id → ordered providers
```

Deterministic selection order:

1. healthy before unhealthy
2. available before unavailable
3. higher priority first
4. stable provider ID tie-breaker

Public operations implemented internally:

```text
register(provider)
replace(provider)
unregister(provider_id)
get(provider_id)
providers()
providers_for_capability(capability_id)
resolve_provider(capability_id)
resolve(capability_id, object_id)
diagnostics()
```

Current baseline policy enables controlled internal provider discovery through
the WNHF package. External entry-point discovery and executor dependency
injection remain disabled.
