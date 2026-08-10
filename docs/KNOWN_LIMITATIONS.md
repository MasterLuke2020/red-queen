# Known Limitations and Deliberate RC1 Boundaries

These items are documented boundaries, not hidden failures.

## Canonical mutating execution is intentionally narrow

RC1 exposes only `lighting.turn_off` as a canonical real-execution action. The semantic model is broader than the productive mutating execution surface.

## Covers

Cover registry/state and `covers.snapshot` are active in the release scope. Canonical mutating `open`, `close`, `stop` or `set_position` actions are not part of the stable RC1 execution surface.

## Climate / temperature

Climate and temperature semantics are planned and are not in the RC1 feature scope.

## Media and notifications

These domains are planned for later feature work.

## Garage / gate actuation

Garage state can already be represented through opening/security models, but active canonical garage-door actuation is planned rather than part of RC1.

## Legacy/development services remain visible

Twenty services are still registered for development lineage or compatibility. `wnhf.public_api` marks them `legacy_or_development` and they are not recommended for new automations.

## Structural registry changes

A complete config-entry reload is safer than assuming every structural object/entity mapping can be hot-swapped through maintenance services. This is especially relevant when entity bindings or platform entity topology changes.

## Logging

INFO-level lifecycle messages are normally hidden when `custom_components.wnhf` is configured at warning level. Absence of a successful reload line at warning level is therefore not evidence that the reload failed.

## External entity quality

Red Queen relies on Home Assistant entity state as technical feedback. Upstream/custom integrations that transiently report incorrect state can affect a guarded execution decision. This was encountered during RC testing with an external OPC UA integration and was diagnosed outside Red Queen; the framework correctly followed the feedback it received.
