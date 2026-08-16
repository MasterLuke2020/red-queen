# Roadmap

The roadmap is directional rather than a promise of exact release numbers or dates.

## 1.0 release-candidate line

The 1.0 RC line expands only through bounded, independently qualified capability
packets. RC5 introduces canonical residential garage open/close execution while
preserving the previously verified lighting, cover, and door lock/unlock contracts.

## Future feature candidates

### Door opener

Evaluate a separate canonical contract for electric residential door openers with
explicit confirmation and appropriate observable feedback semantics.

### Climate / temperature semantics

Introduce semantic temperature, humidity, setpoint and climate-state models/providers
before adding higher-level control decisions.

### Notifications

Add semantic notification/announcement capabilities with routing based on house
context and resident-control principles.

### Media

Add semantic media capabilities without coupling Red Queen core architecture to one
vendor/player implementation.

### Semantic Plant Care

Introduce semantic plant objects with plant species, room/location, watering history
and species-dependent care intervals. Later extensions may incorporate season,
indoor climate, light conditions, soil-moisture sensors, fertilizing, repotting and
vacation-aware care reminders.

## Versioning principle

Compatible feature additions belong in later minor/release-candidate increments;
defect-only corrections use patch releases. A future intentionally incompatible
public contract would require a major version change.
