# WNHF Capability Manager API v1.0

The Capability Manager is the public read-only entry point for semantic
capability inspection and the internal resolution facade used by canonical
Stage-4.7 execution planning.

Actions:

```yaml
action: wnhf.capability_manager
```

```yaml
action: wnhf.capability_list
```

```yaml
action: wnhf.capability_info
data:
  capability_id: lighting
```

Public methods:

```text
async_status()
async_get_capabilities()
async_get_capability(capability_id)
```

The manager orchestrates the Capability Registry and Capability Resolver. It
contains no hardware dispatch implementation. Its public service surface is
read-only, while the canonical execution layer consumes its resolution data to
build guarded execution plans.
