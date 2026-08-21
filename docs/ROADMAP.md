# Roadmap

The roadmap is directional rather than a promise of exact release numbers or dates.

## 1.0 release-candidate line

The 1.0 RC line expands only through bounded, independently qualified capability
packets. RC10 candidate WP-4.7.16.0 completes the native room entity surface on top
of the published, live-verified RC9 baseline.

## Next candidates

### Door opener and cover blades — completed in RC8

WP-4.7.14.0 adds `openings.release`, `covers.blades_open` and
`covers.blades_close`. Door release is explicitly confirmed and closed-door guarded;
all three actions use dispatch-scoped qualification where the final physical effect
is not objectively observable.

### Semantic Plant Care — completed in RC9

RC9 introduced semantic plant objects with species, room/location, persistent
watering history, care intervals and dashboard-ready sensors. Later extensions may
incorporate season, indoor climate, light conditions, soil-moisture sensors,
fertilizing, repotting and vacation-aware care reminders.

### Native room completeness — RC10 candidate

RC10 places every enabled opening on its semantic room device and adds native lock,
door-release, garage and explicit blade controls. Native productive controls enter
the same canonical execution surface as service calls; central diagnostics remain
central.

### Configuration and commissioning

Extend the installation guide into a complete new-house commissioning path and design
a native Home Assistant configuration flow for selecting installation entities and
writing validated integration-owned configuration.

### Functional dashboard

Build a polished Red Queen dashboard on the stable first-version capability surface.

## Deferred feature candidates

### Climate / temperature semantics

Climate work is intentionally deferred while a separate heating integration is being
developed with the heating-system partner. When resumed, introduce semantic
temperature, humidity, setpoint and climate-state models/providers before adding
higher-level control decisions.

### Climate control

After the read semantics are stable, evaluate controlled setpoint writes, operating
modes, safety guards and observable feedback contracts.

## Later feature candidates

### Media

Add semantic media capabilities without coupling Red Queen core architecture to one
vendor or player implementation.

## Versioning principle

Compatible feature additions belong in later minor/release-candidate increments;
defect-only corrections use patch releases. A future intentionally incompatible
public contract would require a major version change.
