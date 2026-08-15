# Red Queen WP-4.7.10.2 — RC3 Candidate Validation

## Scope

Canonical bidirectional cover execution and continuous cover position feedback after the PLC feedback contract was corrected to true OPEN/CLOSED end positions.

## Candidate identity

- Product: Red Queen
- Framework version: `1.0.0-rc3`
- Development baseline: `1.29.1`
- Release baseline: `WP-4.7.10.2`
- Canonical execution API: `1.0`
- Canonical execution contract: `1.5-rc3`

## Implemented contract

- `covers.open` and `covers.close` are canonical real-execution actions.
- OPEN is true only at the fully-open end position.
- CLOSED is true only at the fully-closed end position.
- OPENING and CLOSING identify active movement.
- OPEN=false and CLOSED=false while stationary represents an intermediate position.
- Optional `feedback.closed_percent_entity_id` provides PLC closing degree, where 0%=fully open and 100%=fully closed.
- Native Home Assistant position is exposed as `100 - ClosedPercent`.
- Percentage feedback is supplemental; canonical OPEN/CLOSE safety remains based on binary end-state/movement feedback.
- Opposite-direction automatic reversal is blocked.
- Blade/slat commands remain native-only.
- `SET_POSITION` is not advertised because no target-position command exists.

## Static validation

- Python AST/compile validation: PASS (95 Python files).
- JSON parsing: PASS.
- YAML parsing: PASS.
- Home Assistant manifest version: `1.0.0-rc3`.
- Manifest key ordering preserved from the prior hassfest-passing baseline.
- Home Assistant services count unchanged: 66.
- Canonical real actions: `lighting.turn_on`, `lighting.turn_off`, `covers.open`, `covers.close`.
- Cover Registry parse test: PASS for all 17 reference covers and all 17 ClosedPercent bindings.
- Cover state tests: PASS for OPEN, CLOSED, INTERMEDIATE, OPENING, CLOSING, contradictory OPEN+CLOSED, and position conversion.
- Bidirectional cover pipeline tests: PASS for already-satisfied, already-in-progress, opposite-direction rejection, real CLOSE success, and OPEN regression.

## Live Home Assistant validation

PASS on the reference installation.

Verified live:

- Release metadata and execution-manager readiness matched the RC3 candidate contract.
- Native cover position feedback matched open, closed, and intermediate physical states.
- Canonical `covers.open` real-command path succeeded with feedback confirmation.
- Canonical `covers.open` already-in-progress path suppressed a duplicate command (`EXE-102`).
- Canonical `covers.open` already-satisfied path suppressed a redundant command (`EXE-101`).
- Canonical `covers.close` real-command path succeeded with feedback confirmation.
- Canonical `covers.close` already-in-progress path suppressed a duplicate command (`EXE-102`).
- Canonical `covers.close` already-satisfied path suppressed a redundant command (`EXE-101`).
- Opposite-direction movement guard rejected automatic reversal without dispatching a hardware command.
- Existing RC2 canonical lighting behavior remained operational.

## Result

`WP-4.7.10.2` is LIVE VERIFIED. The candidate may proceed to repository branch CI. A `v1.0.0-rc3` tag/release must not be created until Static repository checks and Home Assistant hassfest pass on the release branch and again on `main` after merge.
