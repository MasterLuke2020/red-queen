# Red Queen 1.0.0-rc11

## WP-4.7.17.0 — Managed Configuration & Commissioning

RC11 makes Red Queen commissioning usable from Home Assistant while keeping registry
ownership explicit and canonical execution safety intact. A configurator-managed
installation can now build and extend the currently supported house registries
without hand-editing semantic IDs or YAML.

### Added

- explicit `uninitialized`, `manual` and `managed` registry ownership modes;
- recovery-mode configuration diagnostics through `wnhf.configuration_snapshot`;
- managed base generation from selected Home Assistant Areas/Floors;
- automatic semantic IDs for rooms and all normal configurator-created objects;
- guided managed configuration for:
  - rooms;
  - impulse-controlled lights (`button.*` command + `binary_sensor.*` feedback);
  - venetian blinds with objective open/closed and movement feedback;
  - optional read-only closed-percent cover feedback and a visible HA position sensor;
  - optional explicit blade-open/blade-close commands;
  - windows and sliding doors;
  - doors with optional motor lock and optional electric door release;
  - garage doors with OSC travel command and optional dedicated STOP command;
  - Plant Care objects with species, location, watering interval and optional moisture
    sensor reference;
- configuration transaction backups under
  `/config/wnhf/house/configuration_backups`;
- localized configurator validation and native-action guard messages.

### Native and execution changes

- Native cover UI is directional only; blade commands remain explicit separate buttons
  so Home Assistant does not present ambiguous tilt controls.
- Blade buttons are unavailable while a cover is moving.
- Garage direction controls are unavailable when the end position is ambiguous.
- `garage.stop` is now a canonical real action when a dedicated STOP command exists.
  STOP is accepted only while motion is objectively observed and is dispatch-scoped;
  Red Queen does not claim the physical stopped position afterward.
- Already-satisfied native cover requests and same-direction in-progress requests are
  treated as normal no-action/in-progress outcomes rather than user-facing failures.
- Native guard failures expose concise localized messages while detailed technical
  causes remain available in Home Assistant logs.
- Plant Care entity names and record-watering controls use user-facing localized names.

### Safety and ownership model

Existing installation-owned registries remain manual and read-only. The configurator
writes only a bundle it created and identifies through its ownership manifest. Every
managed mutation is rendered as a complete draft bundle and loaded through the
production registry loader before replacement. Transactions stage files, create
backups and roll back already-replaced files after write failure.

The configurator does not weaken device safety:

- no arbitrary `SET_POSITION` is advertised for covers with read-only position
  feedback;
- no blade position is invented;
- lock/unlock and electric door release remain blocked while the door is open;
- garage open/close requires a proven opposite stable end position;
- garage STOP requires observed motion and does not infer a resulting position;
- a stopped/intermediate garage state exposes no guessed direction;
- an optional plant moisture sensor is stored as objective input metadata but is not
  used to derive the RC11 watering state.

### Compatibility and public surface

- Home Assistant domain remains `wnhf`.
- Product version: `1.0.0-rc11`.
- Development baseline: WNHF `1.37.0` / `WP-4.7.17.0`.
- 8 semantic capabilities.
- 23 declared semantic actions.
- 16 canonical real-execution action contracts.
- 68 Home Assistant services.
- Canonical execution API remains `1.0`.
- Canonical real-execution contract advances from `2.2-rc10` to `2.3-rc11`
  because `garage.stop` is added.
- No existing object ID, service ID, registry path or persisted qualification record
  is renamed.

### Iterative reference-installation qualification observed on 2026-08-21

The RC11 development package was exercised on the dedicated Home Assistant test
installation during implementation. Observed successful tests include:

- managed registry status and validation;
- room creation from Home Assistant Areas/Floors and duplicate-room rejection;
- automatic IDs and duplicate rejection for impulse lights;
- native light execution with objective feedback and restart persistence;
- recovery/fresh commissioning after `/config/wnhf` was removed on the test system;
- cover open/close, movement state, optional position feedback, dedicated read-only
  position sensor, optional blade commands and moving-state blade guard;
- window and sliding-door state;
- door contact, motor lock, electric door release and open-door guards;
- garage open/close, intermediate-state direction blocking and optional STOP;
- Plant Care creation, watering history, restart persistence and optional stored
  moisture-sensor reference;
- localized native guard messages and guarded/disabled Home Assistant controls.

These observations qualified the implemented paths during development. The exact
consolidated candidate package was subsequently live-regression-tested successfully
on 2026-08-22 before repository publication work.

### Publication gate

Exact-package live qualification passed on 2026-08-22 using the consolidated candidate
ZIP with SHA-256
`9ad0f802d11dce56900323b1a50a1333f3d60d51e26e6522f404ceb7b6e7ce35`.
The remaining publication gates are repository diff review, repository static checks
and Home Assistant hassfest in CI.
