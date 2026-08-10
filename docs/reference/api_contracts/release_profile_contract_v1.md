# WNHF Release Profile Contract v1.1

The current framework baseline is **not yet a public release candidate**.

```text
framework_version: 1.27.0
channel: development
phase: rc_preparation
candidate: null
candidate_assigned: false
```

The semantic version identifies the integration build. It must not be treated
as evidence that an RC has been approved or published.

Current source-of-truth services:

```yaml
action: wnhf.release_info
```

```yaml
action: wnhf.release_scope
```

```yaml
action: wnhf.public_api
```

```yaml
action: wnhf.qualification
```

Canonical productive execution is `wnhf.execution_execute`. The Decision-ID
service `wnhf.execute` is retained as a legacy compatibility path only.

Qualification uses the persistent per-installation Stage-4.7 execution
evidence store and is diagnostic only.
