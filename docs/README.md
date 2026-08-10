# Red Queen 1.0.0-rc1 — Reference Documentation

This package is the **as-built reference documentation** for the live-verified first release candidate of **Red Queen**.

## Release identity

| Item | Value |
|---|---|
| Product | Red Queen |
| Version | `1.0.0-rc1` |
| Release channel | `release_candidate` |
| Release phase | `rc` |
| Candidate | `rc1` |
| Technical Home Assistant domain | `wnhf` |
| Historical development name | WNHF |
| Verified development baseline | `1.27.0` / `WP-4.7.9.1` |
| Canonical execution service | `wnhf.execution_execute` |
| Canonical execution API | `1.0` |
| Canonical execution contract | `1.2-stage4.7.4` |
| RC1 package SHA-256 | `c59388733a488cb9df075e02a5d6bff36398147bb29d6a57465bc495af0ee365` |

Red Queen is a semantic home framework for Home Assistant. It models the house as stable semantic objects and state, evaluates context/rules/policies/decisions, resolves capabilities and providers, and executes explicitly supported actions through contracts, feedback guards and qualification evidence.

The technical identifier `wnhf` deliberately remains unchanged in the 1.0 release line. Existing service IDs, entity unique IDs, configuration paths and persisted evidence therefore remain compatible with the verified development baseline.

## Documentation map

- `RELEASE_STATUS.md` — exact RC1 identity and freeze policy.
- `ARCHITECTURE.md` — system architecture and responsibility boundaries.
- `FEATURE_MATRIX.md` — precise 1.0 RC feature scope.
- `INSTALLATION.md` — installation and lifecycle model.
- `CONFIGURATION.md` — configuration roots and supported YAML models.
- `OPERATIONS.md` — day-to-day operating guidance.
- `DIAGNOSTICS.md` — health, validation and diagnostic surfaces.
- `EXECUTION_CONTRACT.md` — canonical dry-run/execute contract and feedback model.
- `QUALIFICATION.md` — automatic evidence collection and persistence.
- `PUBLIC_API.md` — service classification policy.
- `UPGRADE_AND_COMPATIBILITY.md` — compatibility contract.
- `KNOWN_LIMITATIONS.md` — deliberate RC1 boundaries and operational caveats.
- `ROADMAP.md` — post-1.0 direction without promising a fixed schedule.
- `RC1_VERIFICATION_REPORT.md` — live verification evidence.
- `DEVELOPMENT_LINEAGE.md` — WNHF → Red Queen lineage.
- `reference/services.md` — all 66 registered services.
- `reference/result_codes.md` — canonical `EXE-*` result codes.
- `reference/release_metadata.md` — version/API metadata.
- `reference/terminology.md` — canonical terminology.
- `reference/source_inventory.md` — source snapshot inventory and fingerprints.
- `reference/api_contracts/` — API contract documents copied verbatim from the RC1 source package.
- `handover/RED_QUEEN_HANDOVER_1.0.0-rc1.md` — compact continuation source of truth.

## Status

**Red Queen 1.0.0-rc1 is LIVE VERIFIED.** The RC1 smoke tests passed with runtime health `100`, registry quality `100`, public API classification `66/66`, persistent qualification health `pass`, and no open RC blocker.
