# Contributing to Red Queen

Red Queen is currently in the `1.0.0-rc1` release-candidate phase. The RC line is under **feature freeze**.

## RC rules

During the RC phase, changes should be limited to defects, compatibility fixes, documentation corrections, and release packaging. New functional domains or new canonical mutating actions belong after `1.0.0` unless a release-blocking issue proves they are required.

## Architecture rules

Changes must preserve the separation between:

1. semantic model and state;
2. context/rules/policies/decisions;
3. capabilities and providers;
4. canonical request validation and dry-run planning;
5. real execution;
6. hardware feedback and idempotency;
7. qualification evidence and diagnostics.

A provider must not bypass canonical request validation, and qualification must never be treated as execution authorization.

## Hardware changes

Any change that can cause a real Home Assistant service call or hardware action requires:

- an explicit action contract;
- dry-run validation;
- provider/capability health checks;
- idempotency semantics;
- feedback semantics where the hardware supports feedback;
- a documented regression test.

For toggle-style hardware, never send a blind toggle when feedback shows the requested state is already satisfied.

## Pull requests

A pull request should describe:

- the problem;
- affected public contracts/services;
- whether the change is runtime-functional or documentation-only;
- static validation performed;
- live validation required/performed;
- compatibility or migration impact.

During the RC freeze, a runtime-functional fix should normally result in a new release candidate (`1.0.0-rc2`, etc.) rather than mutating the already verified RC1 artifact.
