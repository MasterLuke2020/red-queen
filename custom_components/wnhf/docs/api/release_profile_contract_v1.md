# Red Queen Release Profile Contract v1.1

The current candidate identity is explicitly assigned by runtime metadata.

```text
product: Red Queen
framework_version: 1.0.0-rc2
development_baseline_version: 1.28.0
release_baseline: WP-4.7.10.1
channel: release_candidate
phase: rc
candidate: rc2
candidate_assigned: true
```

The candidate identity is provided by explicit release metadata; consumers must not
infer RC assignment from a version string alone.

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
