# Operations

## Primary health check

Use the stable service:

```yaml
action: wnhf.system_status
data: {}
```

A healthy idle RC1 runtime is expected to report `status: healthy`, `runtime_ready: true`, `health_score: 100`, `error_count: 0`, and `warning_count: 0`. No canonical execution since startup is informational and does not reduce health.

## Release identity

```yaml
action: wnhf.release_info
data: {}
```

Use this to confirm that the installed package identifies itself as Red Queen `1.0.0-rc1`, candidate `rc1`, with `public_rc_assigned: true`.

## Public API registry

```yaml
action: wnhf.public_api
data: {}
```

This is the authoritative classification of stable, diagnostic, maintenance and legacy/development services.

## Qualification

```yaml
action: wnhf.qualification
data: {}
```

Qualification is a read-only report over runtime readiness and persistent canonical execution evidence.

## Registry validation

```yaml
action: wnhf.validate_registry
data: {}
```

Validation is non-destructive. `system_status` also refreshes validation so stale startup observations do not permanently lower health.

## Logging

The verified installation normally keeps `custom_components.wnhf` at warning level. Successful setup/unload/validation messages are INFO and may therefore be absent from the normal log. Generic Home Assistant warnings that a custom integration has not been tested by Home Assistant are expected for local custom integrations.

## Config-entry reload

A config-entry reload is the preferred method to rebuild the complete Red Queen runtime after structural configuration changes. The RC1 regression gate verified that in-memory last-execution state resets while persistent qualification evidence survives and reloads cleanly.
