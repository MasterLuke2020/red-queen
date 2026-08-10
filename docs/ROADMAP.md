# Roadmap

The roadmap is directional rather than a promise of exact release numbers or dates.

## 1.0 line

The immediate goal after RC1 is release-candidate observation and defect correction only. If RC1 proves stable, it becomes the basis for `1.0.0`. If a defect requires code changes, a new RC is cut and re-verified.

## Post-1.0 feature candidates

### Climate / temperature semantics

Introduce semantic temperature, humidity, setpoint and climate-state models/providers before adding higher-level control decisions.

### Canonical cover execution

Promote cover movement from state/read support to explicit canonical contracts such as open/close/stop/position, with provider validation and feedback confirmation appropriate to the physical hardware.

### Garage / gate execution

Add canonical active access/garage behavior with state-aware guards rather than relying on legacy execution routes.

### Notifications

Add semantic notification/announcement capabilities with routing based on house context and resident-control principles.

### Media

Add semantic media capabilities without coupling Red Queen core architecture to one vendor/player implementation.

## Versioning principle

Compatible feature additions belong in later minor releases; defect-only corrections use patch releases. A future intentionally incompatible public contract would require a major version change.
