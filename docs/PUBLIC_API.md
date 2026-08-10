# Public API Policy

Red Queen RC1 registers exactly **66** `wnhf.*` services and classifies every service exactly once.

| Classification | Count | Meaning |
|---|---:|---|
| Stable public | 8 | Supported public contract for new use |
| Diagnostic public | 34 | Read-only diagnostics / introspection |
| Maintenance public | 4 | Explicit reload/maintenance actions |
| Legacy or development | 20 | Compatibility/internal lineage; not recommended for new automations |

Canonical productive execution is `wnhf.execution_execute`. The legacy Decision-ID entry `wnhf.execute` is intentionally not argument-compatible with the canonical semantic action/target contract.

The authoritative runtime registry is returned by `wnhf.public_api`. RC1 live verification reported `classified_total: 66`, `unique_total: 66`, `duplicates: []`, `complete: true`.

See `reference/services.md` for the complete list and field summaries.
