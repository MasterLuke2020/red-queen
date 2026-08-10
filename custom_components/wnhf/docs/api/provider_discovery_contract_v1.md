# WNHF Provider Discovery API v1.0

Diagnostic action:

```yaml
action: wnhf.provider_discovery
```

WP-4.5.3 scans only:

```text
custom_components.wnhf.providers
```

Eligibility:

- inherits `WNHFProvider`
- concrete class
- declared in scanned module
- `discoverable: true`
- constructor requires no argument, `engine`, or `hass`
- provider contract is valid
- provider ID is unique

Excluded modules:

```text
base
registry
discovery
__init__
_private modules
```

Discovery issues are non-fatal and visible in diagnostics. External entry
points and executor dependency injection remain disabled.
