# Repository Preparation Validation

Generated: 2026-08-10

## Result

**PASS**

- Runtime source under `custom_components/wnhf` is byte-for-byte identical to the live-verified `Red_Queen_1.0.0-rc1.zip` source tree.
- Runtime files compared: 137.
- Python compilation: PASS.
- Manifest identity: `Red Queen / 1.0.0-rc1 / wnhf`.
- Service inventory: 66 unique service definitions.
- JSON parsing: PASS.
- Frozen RC1 source checksum verification: PASS.
- Active HACS metadata: intentionally disabled pending publication decisions.

## Local verifier

Run:

```bash
python tools/verify_repository.py
```

This check is intentionally complementary to, not a replacement for, Home Assistant hassfest and HACS validation.
