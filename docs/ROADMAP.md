# Roadmap

The roadmap is directional rather than a promise of exact release numbers or dates.

## 1.0 release-candidate line

The 1.0 RC line expands only through bounded, independently qualified capability
packets. RC8 candidate WP-4.7.14.0 promotes the existing venetian-blind blade and
electric door-opener commands into the canonical execution surface on top of the
live-verified RC7 baseline.

## Next candidates

### Door opener and cover blades

WP-4.7.14.0 adds `openings.release`, `covers.blades_open` and
`covers.blades_close`. Door release is explicitly confirmed and closed-door guarded;
all three actions use dispatch-scoped qualification where the final physical effect
is not objectively observable.

### Semantic Plant Care

Introduce semantic plant objects with species, room/location, watering history and
species-dependent care intervals. Later extensions may incorporate season, indoor
climate, light conditions, soil-moisture sensors, fertilizing, repotting and
vacation-aware care reminders.

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
