# Roadmap

The roadmap is directional rather than a promise of exact release numbers or dates.

## 1.0 release-candidate line

The 1.0 RC line expands only through bounded, independently qualified capability
packets. RC6 adds the live-verified Semantic Notifications Core while preserving the
previously verified lighting, cover, door lock/unlock and garage contracts.

## Next candidates

### Notification routing / announcements

A possible WP-4.7.13.2 may add context-based routing, multiple semantic recipients,
house announcements and TTS/Sonos delivery. These are not part of RC6.

### Climate / temperature semantics

Introduce semantic temperature, humidity, setpoint and climate-state models/providers
before adding higher-level control decisions.

### Climate control

After the read semantics are stable, evaluate controlled setpoint writes, operating
modes, safety guards and observable feedback contracts.

## Later feature candidates

### Media

Add semantic media capabilities without coupling Red Queen core architecture to one
vendor or player implementation.

### Semantic Plant Care

Introduce semantic plant objects with species, room/location, watering history and
species-dependent care intervals. Later extensions may incorporate season, indoor
climate, light conditions, soil-moisture sensors, fertilizing, repotting and
vacation-aware care reminders.

### Door opener

Evaluate a separate canonical contract for electric residential door openers with
explicit confirmation and appropriate observable feedback semantics.

## Versioning principle

Compatible feature additions belong in later minor/release-candidate increments;
defect-only corrections use patch releases. A future intentionally incompatible
public contract would require a major version change.
