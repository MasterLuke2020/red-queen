# WNHF Capability Contract v1.0

WP-4.6.1 introduces immutable semantic capability declarations.

Each capability declares:

```text
capability_id
version
name
description
kind
actions
required_provider_capabilities
priority
enabled
```

This package does not yet migrate execution to the capability layer.

Diagnostic action:

```yaml
action: wnhf.capability_registry
```
