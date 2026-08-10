# WNHF Generic Execution Qualification Contract v1.1

Service:

```yaml
action: wnhf.execution_qualification
```

The active qualification architecture is the Stage-4.7 semantic execution
evidence pipeline.

Qualifying execution results are collected automatically:

```text
EXE-000 -> real_success
EXE-101 -> idempotency
```

Evidence is persisted atomically per installation at:

```text
/config/wnhf/qualification/execution_evidence_store.json
```

The current store contract uses schema `1.0` and store implementation
`1.2-stage4.7.7.1`. Evidence is restored after Home Assistant restarts and
config-entry reloads.

`wnhf.provider_qualification` is a provider-centric diagnostic projection of
this same canonical store. It is not a second evidence source.

Qualification is diagnostic evidence only. It does not authorize execution,
weaken provider health checks, bypass confirmation requirements, disable
idempotency guards, or replace required hardware feedback verification.
