# Red Queen

**Red Queen** is a semantic home framework for Home Assistant. Instead of treating a smart home as a loose collection of switches, it models the house as semantic objects and state, evaluates context/rules/policies/decisions, resolves capabilities and providers, and executes explicitly supported actions through contracts and feedback-aware guards.

> **Current release:** `1.0.0-rc1` — LIVE VERIFIED  
> **Technical Home Assistant domain:** `wnhf`  
> **Development lineage:** WNHF `1.27.0` / `WP-4.7.9.1`

## What Red Queen does

Red Queen provides a stable framework around the home rather than another device protocol. The current 1.0 release candidate includes:

- semantic house and room modelling;
- lighting state and canonical `lighting.turn_off` execution;
- opening state and snapshots;
- cover state and snapshots;
- security aggregation;
- context, rules, policies and decisions;
- provider and capability resolution;
- canonical dry-run and execution contracts;
- feedback guards and idempotency;
- persistent qualification evidence;
- runtime health, validation and diagnostics.

The stable canonical mutating execution surface is intentionally narrower than the semantic model. Canonical cover actuation, climate/temperature, media, notifications and active garage/gate control are not part of the 1.0 RC execution surface yet.

See [Feature Matrix](docs/FEATURE_MATRIX.md) for the exact scope.

## Technical identity

The public product name is **Red Queen**. For compatibility, the Home Assistant integration domain remains `wnhf` in the 1.0 release line. Existing service IDs, entity unique IDs, configuration paths and persisted qualification evidence are therefore not renamed.

Canonical execution entry point:

```text
wnhf.execution_execute
```

The older Decision-ID service `wnhf.execute` remains a legacy compatibility path and is not recommended for new automations.

## Installation

Until the public repository/release channel is finalized, install manually:

1. Copy `custom_components/wnhf` into your Home Assistant configuration directory as `/config/custom_components/wnhf`.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add Integration** and add **Red Queen**.

For the verified Docker development installation, see [Installation](docs/INSTALLATION.md).

## RC1 verification

Red Queen `1.0.0-rc1` was live-verified on the reference installation with:

- runtime health: `100`;
- registry quality: `100`;
- public API classification: `66/66`;
- canonical `EXE-101` idempotency: verified;
- canonical `EXE-000` real hardware success: verified;
- config-entry reload and persistent qualification: verified;
- persistent evidence at RC1 verification: `11` successful passes;
- open RC blockers: `0`.

The full evidence is documented in [RC1 Verification Report](docs/RC1_VERIFICATION_REPORT.md).

## Repository status

This repository snapshot is **private-publication ready** for `github.com/MasterLuke2020/red-queen`. Repository ownership, maintainer metadata and the MIT license are finalized. The runtime logic remains frozen to the live-verified RC1 package; only publication metadata in `manifest.json` differs from the archived runtime artifact. Independent brand assets and optional HACS publication remain intentionally deferred.

## Documentation

Start with [Documentation Index](docs/README.md). Key references:

- [Architecture](docs/ARCHITECTURE.md)
- [Execution Contract](docs/EXECUTION_CONTRACT.md)
- [Qualification](docs/QUALIFICATION.md)
- [Public API](docs/PUBLIC_API.md)
- [Known Limitations](docs/KNOWN_LIMITATIONS.md)
- [Roadmap](docs/ROADMAP.md)
- [RC1 Soak Plan](docs/RC1_SOAK_PLAN.md)
- [Release Process](RELEASE_PROCESS.md)

## Contributing

The 1.0 RC line is under feature freeze. Bug fixes must preserve the canonical contracts or deliberately create a new RC with full regression validation. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Red Queen is licensed under the [MIT License](LICENSE).

Copyright (c) 2026 Weidner Net - Ing. Lukas Weidner.
