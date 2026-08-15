# Red Queen 1.0.0-rc4

## WP-4.7.11.1 — Canonical Door Lock / Unlock Execution

RC4 promotes the existing motor-lock Access model into the canonical semantic
execution surface.

### Added

- `openings.lock` canonical real execution.
- `openings.unlock` canonical real execution.
- Explicit confirmation requirement for both lock actions.
- Closed-door preflight guard before lock-state mutation.
- Required motor-lock feedback confirmation after command dispatch.
- Idempotent no-command behavior when the requested lock state already exists.

### Safety contract

A canonical lock/unlock request is executable only when exactly one semantic opening
object is targeted, no parameters are supplied, `confirmed: true`, the object declares
the corresponding Access lock capability, the Access runtime is available, the door
contact reports closed, and lock feedback reports a stable `locked` or `unlocked`
state.

An already-satisfied request returns the canonical no-action path without sending a
second hardware command. A dispatched command must be followed by the requested lock
feedback before it is considered successful.

Door-opener and garage commands remain outside canonical execution in this work
package.
