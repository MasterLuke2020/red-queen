# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. It models the house
as semantic objects and state, resolves native/canonical controls, and exposes a
stable Home Assistant surface for commissioning, operation and diagnostics.

> **Current candidate:** `1.0.0-rc12` — FINAL EXACT PACKAGE LIVE VERIFIED / CI PASS
> **Technical Home Assistant domain:** `wnhf`
> **Development lineage:** WNHF `1.38.0` / `WP-4.7.18.0`

## RC12 candidate changes

RC12 adds the **Generated Dashboard Foundation** on top of the RC11 managed
configuration and native entity surface.

- Adds a deterministic dashboard model derived from the semantic house registry.
- Resolves current Home Assistant entity IDs through stable Red Queen unique IDs.
- Generates an integration-owned native Lovelace dashboard at `/red-queen`.
- Adds overview, floor views, room subviews, Plant Care and System/Diagnostics views.
- Uses native Home Assistant cards only; no mandatory custom frontend cards are
  required.
- Adds explicit **Dashboard erstellen** / **Dashboard aktualisieren** lifecycle actions.
- Preserves existing user dashboards and never rewrites the default Lovelace setup.
- Supports both managed and manual Red Queen registries; manual registries remain
  read-only for semantic configuration.
- Detects renderer/model changes through a deterministic dashboard digest.
- Restores the generated dashboard after Home Assistant restart without regenerating
  it implicitly.
- Keeps all physical safety/guard logic in the canonical Red Queen native layer.
- Reduces large validator sensor attributes so Recorder no longer receives oversized
  diagnostic payloads.

## Current canonical real-execution surface

```text
lighting.turn_on
lighting.turn_off
covers.open
covers.close
covers.blades_open
covers.blades_close
garage.open
garage.close
garage.stop
openings.lock
openings.unlock
openings.release
notifications.send
notifications.announce
notifications.route
plants.record_watering
```

Canonical execution entry point: `wnhf.execution_execute`
Canonical execution API: `1.0`
Canonical real-execution contract remains `2.3-rc11` because RC12 changes the
presentation/dashboard layer, not the execution contract.

## Candidate status

The exact RC12 candidate package was clean-installed and live-qualified on the
dedicated Home Assistant test system on 2026-08-24. The qualified package contains
174 integration files and has SHA-256:

`d1c683f56990ed14aa7e488564dad67d008fbd483ec3353ca793af56fec135d7`

The exact package passed registry loading/validation, dashboard preview and creation,
`168/168` native entity binding, overview/floor/room/Plant Care/System navigation,
restart persistence and post-restart `Status: aktuell`. No Red Queen dashboard errors,
tracebacks or oversized Recorder attribute warnings were observed.

Home Assistant hassfest required the explicit `lovelace` dependency declaration.
After that metadata-only correction, static repository checks and hassfest passed on
the frozen RC12 integration source. The rebuilt final package was then re-tested for
startup, dashboard restore and restart persistence. The remaining gate is publication.

See `docs/RC12_CANDIDATE_VALIDATION.md` and
`custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc12.md`.

## Installation

Copy `custom_components/wnhf` to `/config/custom_components/wnhf`, restart Home
Assistant, and add/reload **Red Queen** through **Settings → Devices & services**.

Installation-owned semantic data remains below `/config/wnhf`. Existing manual
registries are not silently adopted or rewritten by the managed configurator.

## License

Red Queen is licensed under the MIT License.

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
