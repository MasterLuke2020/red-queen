# Roadmap

The roadmap is directional rather than a promise of exact release numbers or dates.

## 1.0 release-candidate line

The 1.0 RC line expands only through bounded, independently qualified capability
packets.

### Managed configuration and commissioning — completed in RC11

RC11 added explicit registry ownership modes and the transaction-safe Managed
configuration path for rooms, lights, covers, openings, garage and Plant Care.

### Generated Dashboard Foundation — RC12

RC12 adds an integration-owned native Home Assistant dashboard generated from the
semantic house model and native Red Queen entity surface.

The RC12 dashboard provides:

- overall house overview;
- floor navigation and room subviews;
- lighting, covers, openings/access and garage projections;
- Plant Care and System/Diagnostics views;
- stable unique-ID based entity binding;
- explicit create/update lifecycle;
- deterministic update detection;
- restart persistence;
- native HA cards with no mandatory custom frontend dependency.

The dashboard never becomes a second safety engine. Physical action guards remain in
canonical Red Queen execution.

## Next candidates

### Dashboard refinement

Continue visual/UX refinement only where it can remain deterministic, native and
safe. Consider user-selectable presentation preferences without making dashboard
correctness depend on custom frontend cards.

### Commissioning refinement

Continue improving managed editing, object maintenance, diagnostics and migration
guidance without silently taking ownership of manual registries.

### Plant Care extensions

Potential later work includes season, indoor climate, light conditions,
soil-moisture-aware recommendations, fertilizing, repotting and vacation-aware care.

## Deferred feature candidates

### Climate / temperature semantics

Climate work remains intentionally deferred while the separate heating integration
is developed with the heating-system partner.

### Media

Add semantic media capabilities without coupling Red Queen core architecture to one
vendor or player implementation.

## Versioning principle

Compatible feature additions belong in later minor/release-candidate increments;
defect-only corrections use patch releases. A future intentionally incompatible
public contract would require a major version change.
