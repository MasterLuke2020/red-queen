# Red Queen Release Profile Contract v1.1

The current candidate identity is explicitly assigned by runtime metadata.

```text
product: Red Queen
framework_version: 1.0.0-rc9
development_baseline_version: 1.35.0
release_baseline: WP-4.7.15.0
channel: release_candidate
phase: rc
candidate: rc9
candidate_assigned: true
```

The candidate identity is provided by explicit release metadata; consumers must not
infer RC assignment from a version string alone.

Source-of-truth services are `wnhf.release_info`, `wnhf.release_scope`,
`wnhf.public_api` and `wnhf.qualification`.

Canonical productive execution is `wnhf.execution_execute`. The Decision-ID service
`wnhf.execute` is retained as a legacy compatibility path only. Qualification uses
the persistent per-installation Stage-4.7 execution evidence store and is diagnostic
only.
