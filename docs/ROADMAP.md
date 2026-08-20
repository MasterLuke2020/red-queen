# Roadmap

The roadmap is directional rather than a promise of exact release numbers or dates.

## 1.0 release-candidate line

The 1.0 RC line expands only through bounded, independently qualified capability
packets. RC7 candidate WP-4.7.13.2 adds native notification routing and announcements
on top of the live-verified RC6 Semantic Notifications Core.

## Next candidates

### Notification routing / announcements qualification

WP-4.7.13.2 implements provider-neutral announcement targets, native TTS/Sonos
delivery and profile/priority channel routing. Static and reference-installation live
qualification must complete before RC7 publication.

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
