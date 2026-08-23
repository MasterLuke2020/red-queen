# Red Queen 1.0.0-rc11 — Static Candidate Validation

Generated: 2026-08-21T21:44:48.919642+00:00

Result: **PASS**

Validated on the consolidated candidate source:

- Python syntax/compile check: PASS
- JSON parsing for manifest/release/translations: PASS
- YAML parsing for Home Assistant services and canonical API contracts: PASS
- Product/version metadata alignment: PASS
- Semantic capabilities: 8
- Declared semantic actions: 23
- Canonical real-execution actions: 16
- Home Assistant services: 68
- `garage.stop` present in semantic capability, dry-run and real-execution contracts: PASS
- `wnhf.configuration_snapshot` included in the public service classification: PASS
- Managed registry isolated transaction test: PASS
- Managed room/light/cover/window/door/garage/plant bundle validation: PASS
- Duplicate semantic object rejection: PASS
- Test-installation entity/name markers absent from integration source: PASS
- Python bytecode/cache files excluded from candidate package: PASS

This static validation does not replace the exact-package Home Assistant regression
described in `RC11_CANDIDATE_VALIDATION.md`, nor repository CI/hassfest.
