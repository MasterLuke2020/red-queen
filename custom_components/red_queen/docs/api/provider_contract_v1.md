# WNHF Provider Contract v1.0

Status: **stable contract for the current release-preparation baseline**.

A provider supplies:

```text
provider_id
provider_version
supported_capabilities()
snapshot()
resolve()
qualification()
runtime_state()
diagnostics()
metadata()
async_setup()
async_unload()
```

Provider IDs use:

```text
provider.<namespace>.<name>[.<name>...]
```

Versions use semantic versioning:

```text
x.y.z
```

Current discovery policy:

- controlled internal package discovery is enabled;
- external entry-point discovery remains disabled;
- provider dependency injection remains disabled.

Provider selection is deterministic and prioritizes health, availability,
priority and finally stable provider ID ordering.

Diagnostic action:

```yaml
action: wnhf.provider_contract
```

## Capability ID format

Capability IDs may be either top-level or hierarchical:

```text
lighting
access.lock
climate.set_temperature
```

They use lowercase semantic segments with underscores and optional dots.
