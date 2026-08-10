# WNHF Provider Qualification API Contract v1.1

Service:

```yaml
action: wnhf.provider_qualification
```

WP-4.7.8.3 makes provider qualification an installation-neutral diagnostic
view over the canonical Stage-4.7 semantic execution evidence store.

The framework no longer ships curated provider profiles or real-hardware
verification results from the WNHF development installation. A provider is
reported as `framework_verified` only when the current installation's
persistent execution evidence contains framework-verified evidence for that
provider.

Current qualification statuses:

- `unverified` — no canonical execution evidence exists for the provider.
- `evidence_present` — evidence exists but is not framework-verified.
- `framework_verified` — at least one framework-verified execution evidence
  record exists for the provider.

Qualification is diagnostic evidence only. It does not authorize execution,
weaken confirmation policies, or bypass feedback guards.

The canonical evidence file is:

```text
/config/wnhf/qualification/execution_evidence_store.json
```

The former Stage-4.4 `provider_evidence_store.json` is no longer loaded or
consumed. WNHF intentionally leaves an existing legacy file untouched instead
of deleting installation data during migration.
