# Release Status

## Current candidate

**Red Queen 1.0.0-rc11 — LIVE VERIFIED**

RC11 is based on the published, live-verified RC10 baseline and advances the
development lineage to WNHF `1.37.0` / `WP-4.7.17.0`.

The release adds a managed Home Assistant commissioning/configuration path for the
currently supported semantic house registries while preserving existing manual
registries as read-only. It also adds canonical guarded `garage.stop`.

## RC11 exact-package qualification

The exact consolidated candidate package was installed on the dedicated Home
Assistant test system and qualified on 2026-08-22.

Observed PASS results included:

- managed registry creation/status/validation and fresh commissioning recovery;
- automatic room/object IDs and duplicate rejection;
- native impulse-light execution with objective feedback;
- cover open/close, movement state, read-only position and blade movement guard;
- window and sliding-door state;
- door motor-lock/electric-release configuration and open-door safety guard;
- garage open/close, intermediate-state direction blocking and dedicated STOP;
- Plant Care creation, watering history and restart persistence;
- optional plant moisture-sensor reference stored without driving care state;
- localized configurator/native guard messages;
- restart persistence of the managed registry and native entities.

The exact candidate ZIP qualified in that test had SHA-256:

`9ad0f802d11dce56900323b1a50a1333f3d60d51e26e6522f404ceb7b6e7ce35`

Home Assistant hassfest passed on the RC11 release branch on 2026-08-23. Repository
static verification must pass on the final release commit before publication.

## Compatibility and safety

- Home Assistant integration domain remains `wnhf`.
- Canonical execution entry remains `wnhf.execution_execute`.
- Canonical execution API remains `1.0`.
- 8 capabilities, 23 semantic actions, 16 canonical real contracts and 68 services.
- Garage STOP is dispatch-scoped and does not claim a resulting physical position.
- Cover position is read-only and arbitrary `SET_POSITION` remains disabled.
- Blade position, latch release, physical door opening and physical watering are not
  claimed without objective evidence.
- Optional plant moisture input is metadata only in RC11.

## RC policy

During the RC line, capability additions are accepted only as bounded work packages
with explicit contracts, static validation, isolated behavior validation, live Home
Assistant validation, regression checks and a new immutable release candidate. A
published RC is never silently overwritten.
