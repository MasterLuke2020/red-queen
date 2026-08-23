# Roadmap

The roadmap is directional rather than a promise of exact release numbers or dates.

## 1.0 release-candidate line

The 1.0 RC line expands only through bounded, independently qualified capability
packets.

### Door opener and cover blades — completed in RC8

RC8 added canonical electric door release and explicit cover blade commands with
dispatch-scoped qualification where final physical state is not objectively
observable.

### Semantic Plant Care — completed in RC9

RC9 introduced semantic plants, persistent watering history, room-attached care
sensors and canonical record-watering actions.

### Native room completeness — completed in RC10

RC10 projected enabled openings and productive controls onto their semantic room
devices and routed native controls through canonical execution.

### Managed configuration and commissioning — RC11

RC11 adds explicit registry ownership modes and a transaction-safe managed
configurator. New installations can create a base from Home Assistant Areas/Floors
and add rooms, impulse lights, venetian blinds, windows, sliding doors, doors, garage
doors and Plant Care objects without manually creating semantic IDs.

RC11 also adds guarded canonical `garage.stop` for installations with a dedicated
STOP command. Optional plant moisture input is stored but intentionally does not
drive watering decisions yet.

## Next candidates

### Functional dashboard

Build a polished Red Queen dashboard on the stable semantic/native capability
surface, with room-focused controls and diagnostics.

### Commissioning refinement

Continue improving managed editing, object maintenance, diagnostics and migration
guidance without silently taking ownership of manual registries.

### Plant Care extensions

Potential later work includes season, indoor climate, light conditions,
soil-moisture-aware recommendations, fertilizing, repotting and vacation-aware care.

## Deferred feature candidates

### Climate / temperature semantics

Climate work remains intentionally deferred while the separate heating integration
is developed with the heating-system partner. When resumed, introduce semantic
temperature, humidity, setpoint and climate-state models/providers before adding
higher-level control decisions.

### Climate control

After read semantics are stable, evaluate controlled setpoint writes, operating
modes, safety guards and observable feedback contracts.

## Later feature candidates

### Media

Add semantic media capabilities without coupling Red Queen core architecture to one
vendor or player implementation.

## Versioning principle

Compatible feature additions belong in later minor/release-candidate increments;
defect-only corrections use patch releases. A future intentionally incompatible
public contract would require a major version change.
