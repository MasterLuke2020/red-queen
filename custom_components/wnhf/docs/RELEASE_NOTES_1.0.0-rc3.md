# Red Queen 1.0.0-rc3

## WP-4.7.10.2 — Canonical Bidirectional Cover Execution & Position Feedback

RC3 promotes safely provable cover movement in both directions into the canonical
semantic execution surface and adds objective continuous position feedback.

### Added

- Canonical `covers.open`.
- Canonical `covers.close`.
- Object-level semantic cover capability declarations with command and feedback bindings.
- Optional Registry binding `feedback.closed_percent_entity_id`.
- Native Home Assistant cover position derived from PLC closing degree:
  `current_cover_position = 100 - closed_percent`.
- Feedback-guarded bidirectional cover pipeline.
- `EXE-102 already_in_progress` when the requested direction is already active.

### Guard behavior

For both OPEN and CLOSE:

- Requested end state already reported -> `EXE-101`, no command.
- Requested movement already active -> `EXE-102`, no duplicate command.
- Opposite movement currently active -> request rejected; no automatic reversal.
- Stable opposite/intermediate state -> exactly one directional command, then requested
  movement or requested end-state feedback must be observed.
- Unavailable or contradictory binary feedback blocks execution.

### Position feedback

PLC `ClosedPercent` is defined as 0%=fully open and 100%=fully closed. Home Assistant
cover position uses the inverse convention, therefore Red Queen exposes:

`current_cover_position = 100 - ClosedPercent`

The percentage is supplemental feedback. Canonical OPEN/CLOSE safety and completion
remain based on the binary OPEN/CLOSED/OPENING/CLOSING signals. Position mismatch
diagnostics do not automatically dispatch or reverse hardware commands.

`SET_POSITION` is intentionally not advertised because RC3 has feedback only, not a
position target command.

Blade/slat commands remain native-only because objective blade-position feedback is
not available.

### Compatibility

- Technical domain remains `wnhf`.
- No Home Assistant service was added or removed.
- Existing native lights/covers remain compatible.
- Lighting canonical execution from RC2 is unchanged.
- Existing qualification evidence store remains compatible.
