# Red Queen 1.0.0-rc10

## WP-4.7.16.0 — Native Room Completeness

RC10 completes the Home Assistant room-device projection for the existing first
functional Red Queen scope.

### Added

- one native room-associated binary sensor for every enabled semantic opening;
- native room lock entities for configured motor locks;
- native confirmed door-release buttons;
- one native garage cover for each configured garage door;
- explicit blade-open and blade-close buttons for capable venetian blinds.

### Canonical native execution

Native lights, covers, blade controls, locks, door release, garage controls and Plant
Care buttons now enter `wnhf.execution_execute`. They retain semantic target IDs,
provider validation, feedback guards, explicit confirmation policy and persistent
qualification. A rejected guard is surfaced as a Home Assistant error and dispatches
no technical command.

### Device organization

Physical state and controls attach to the Red Queen room selected by the object's
registry `room` field. Central framework health, security and aggregate diagnostics
remain on central module devices. No new mapping file is required.

### Compatibility and safety

- technical integration domain remains `wnhf`;
- public service and action IDs are unchanged;
- 67 services, 8 capabilities, 22 semantic actions and 15 canonical real contracts;
- access controls keep explicit confirmation and objective feedback guards;
- blade position, latch release, physical opening and unobserved garage direction
  are not claimed;
- Plant Care and notification behavior remain compatible with RC9.

### Qualification status

Static verification and reference-installation live qualification passed on
2026-08-21. Native office lighting/blades, entrance locks and door release, opening
state, garage open/close, room association and restart stability were observed. Final
runtime health was 100 with zero Red Queen errors and warnings. See
`docs/RC10_CANDIDATE_VALIDATION.md`.
