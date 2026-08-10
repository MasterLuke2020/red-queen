# Architecture

## Purpose

Red Queen is not merely an actuator abstraction. Its core role is to maintain a semantic model of the house, derive context, evaluate rules/policies/decisions, resolve runtime capabilities, and perform only explicitly contracted real-world actions with observable feedback.

## Canonical architecture

```text
Home Assistant entities / hardware integrations
                    │
                    ▼
            Semantic House Model
      Rooms / Lights / Openings / Covers
                    │
                    ▼
          State aggregation / Context
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        Rules     Policies  Decisions
          └─────────┼─────────┘
                    ▼
             Capability Layer
       definitions / resolver / manager
                    │
                    ▼
              Provider Layer
       availability / health / contracts
                    │
                    ▼
          Canonical Execution Layer
        dry-run → promotion → dispatch
                    │
                    ▼
             Hardware Feedback
                    │
                    ▼
       Qualification / Runtime Health
```

## Responsibility boundaries

### Semantic house model

Stable object IDs separate Red Queen semantics from Home Assistant entity IDs. Rooms own semantic lights/covers/openings; hardware entity IDs are implementation bindings rather than the primary identity.

### Rules, context, policies and decisions

These layers explain *what the house means* and *whether/recommendation logic applies*. They do not bypass execution contracts or provider safety checks.

### Capabilities

Capabilities answer whether a semantic domain/action is defined and can resolve to healthy providers. RC1 deliberately distinguishes semantic readiness from real execution enablement.

### Providers

Providers translate semantic operations into technical capabilities and own hardware-specific validation/feedback requirements. Provider availability/health participates in execution readiness.

### Canonical execution

The Stage-4.7 semantic path is the productive route. Validation builds a non-dispatching plan first; only an execution request can promote that validated plan and dispatch to a provider.

### Feedback guard

Where a provider defines feedback as required, Red Queen treats real observed state as part of the execution contract. RC1's verified `lighting.turn_off` toggle strategy will not blindly pulse hardware when feedback already reports off.

### Qualification

Qualification records verified outcomes; it does not authorize future executions. The provider, action contract, confirmation rules and live feedback remain authoritative for each new request.

## Resident-control principle

The framework architecture is designed so that higher-level intelligence does not replace normal manual control. Red Queen can reason, recommend, validate and execute through explicit contracts; it should not make the basic house unusable when optional intelligence is unavailable.
