# Red Queen 1.0.0-rc5

## WP-4.7.12.1 — Canonical Garage Open / Close Execution

RC5 promotes residential garage-door direction into the canonical semantic execution
path while keeping the hardware OSC detail internal.

### Added

- semantic `garage` capability;
- `garage.snapshot` read action;
- canonical `garage.open` and `garage.close` real execution;
- dedicated `GarageCapabilityProvider`;
- explicit confirmation for both garage directions;
- stable-end-position preflight guards and terminal feedback confirmation.

### Safety contract

A directional request may dispatch exactly one OSC pulse only from the proven opposite
end position. Already-satisfied requests are idempotent and send no command. Moving,
intermediate, unavailable, and contradictory feedback states reject without a pulse.

Canonical `garage.stop` and `garage.toggle` are intentionally not exposed because a
residential OSC input is stateful and non-directional. Red Queen never guesses the
next OSC direction from an ambiguous intermediate state.

### Compatibility

No Registry migration is required. The technical Home Assistant domain remains
`wnhf`; canonical execution remains `wnhf.execution_execute` API 1.0. Existing
lighting, covers, and door lock/unlock contracts are preserved.

### Validation state

Static and isolated behavior validation passed. Live reference-installation
verification passed on 2026-08-16. WP-4.7.12.1 is LIVE VERIFIED; publication of
the immutable RC5 release remains a separate release-process step.
