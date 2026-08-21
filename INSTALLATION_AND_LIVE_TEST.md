# Red Queen 1.0.0-rc10 — Installation and live qualification

Status: static verification and reference-installation live qualification required
for WP-4.7.16.0.

## 1. Back up and install

1. Back up `/config/custom_components/wnhf` and `/config/wnhf`.
2. Replace `/config/custom_components/wnhf` with the packaged RC10 integration.
3. Preserve every installation-owned registry and persistent-state file below
   `/config/wnhf`.
4. Restart Home Assistant completely.

RC10 does not add or rewrite registry files. Existing `rooms.yaml`, `lights.yaml`,
`covers.yaml`, `openings.yaml`, optional `plants.yaml` and notification targets remain
installation-owned.

## 2. Post-restart preflight

Confirm:

- Red Queen `1.0.0-rc10`;
- WNHF `1.36.0` / `WP-4.7.16.0`;
- phase name `Release Candidate 10`;
- runtime ready, health 100 and no Red Queen errors/warnings;
- 8 capabilities, 22 semantic actions and 15 canonical real contracts;
- the `lock` entity platform loaded without setup errors.

## 3. Native room inventory

For the Weidnerhome reference registry, confirm:

- 21 native `binary_sensor.wnhf_opening_*` entities;
- 2 native `lock.wnhf_lock_*` entities;
- 2 native `button.wnhf_door_release_*` entities;
- 34 native `button.wnhf_blades_open_*` / `wnhf_blades_close_*` entities;
- 1 native `cover.wnhf_garage_*` entity;
- the existing 13 Plant Care sensors and 13 watering buttons;
- existing native room lights and venetian-blind covers remain present.

Open representative Red Queen room devices (office, vestibule, dining room,
bathroom, gallery, hobby room and garage). Every physical object and control must be
attached to its configured room. Central health, security and aggregate diagnostics
must remain on their central module devices.

## 4. Passive state tests

Open and close representative windows, doors and the garage door. Confirm that the
corresponding native opening binary sensor follows objective feedback. Lock/unlock
feedback must update the native lock entity. No native adapter may invent a garage
direction or blade position that is not objectively observable.

## 5. Native control tests

Run only safe, observed actions:

1. Toggle one native Red Queen light off/on.
2. Open/close one native Red Queen blind.
3. Press its explicit blade-open and blade-close buttons while stationary.
4. Lock/unlock one closed test door through its native lock entity.
5. Press one door-release button only while the door is proven closed.
6. Open/close the garage from the required opposite stable end positions.
7. Record a watering event only after that plant was physically watered.

Each action must appear as `wnhf.execution_execute` evidence with the correct semantic
action ID. Exactly one technical command may be dispatched per accepted request.

## 6. Rejection tests

Confirm that these native requests reject visibly and dispatch no command:

- blade action while its cover is moving;
- door release while the door contact reports open;
- lock/unlock while the door is open;
- garage direction from moving, intermediate, unavailable or contradictory state.

## 7. Restart and regression

Restart Home Assistant completely. Confirm entity/device/area associations remain
stable, Plant Care history persists, and representative notification routes plus
canonical dry-runs for every existing domain still pass.

Record only observed results in `docs/RC10_CANDIDATE_VALIDATION.md`. Publication
requires final health 100, runtime ready, zero Red Queen errors and zero warnings.
