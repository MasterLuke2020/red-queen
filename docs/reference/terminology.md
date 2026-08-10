# Terminology

| Term | Meaning in Red Queen |
|---|---|
| Semantic object | Stable Red Queen identity representing a house object independent of a specific HA entity ID |
| Provider | Runtime implementation binding semantic capabilities to technical entities/behavior |
| Capability | Declared semantic ability resolved through provider availability/health |
| Declared action | Action exists in semantic capability registry |
| Semantically ready | Action resolves to available and healthy providers |
| Real execution enabled | Canonical real-execution contract exists for that action |
| Executable now | Semantically ready and real execution enabled |
| Dry run | Full preflight/plan generation with no hardware dispatch |
| Promotion | Conversion of a validated dry-run plan into an execution plan |
| Feedback guard | Provider rule that uses observed state before/after dispatch to avoid blind actuation and confirm effects |
| Qualification | Persistent evidence from qualifying canonical execution outcomes; not authorization |
| Canonical execution | Stage-4.7 semantic productive path through `wnhf.execution_execute` |
| Legacy execution | Older Decision-ID/specialized paths retained for compatibility or diagnostics |
| Release scope | Domains that count toward current release readiness vs planned domains |
| RC freeze | No new RC1 features; only defects justify a new candidate |
| WNHF | Historical development name and retained technical namespace/domain |
| Red Queen | Public product/framework name |
