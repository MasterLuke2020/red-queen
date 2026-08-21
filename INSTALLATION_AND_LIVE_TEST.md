# Red Queen 1.0.0-rc9 — Installation and live qualification

Status: static verification and reference-installation live qualification required
for WP-4.7.15.0.

## 1. Back up the installation

Back up `/config/custom_components/wnhf` and `/config/wnhf`. RC9 never overwrites
installation-owned registry data automatically.

## 2. Add the Plant Care registry

Copy repository file `configuration/plants.yaml` to:

```text
/config/wnhf/house/registry/plants.yaml
```

Do not create `/config/wnhf/plant_care/watering_history.json` manually. Red Queen
creates it atomically after the first real `plants.record_watering` action. If the
file does not exist, all plants correctly start as `unknown`.

## 3. Install the candidate

1. Replace `/config/custom_components/wnhf` with the packaged RC9 integration.
2. Preserve all other installation-owned `/config/wnhf` files.
3. Restart Home Assistant completely.
4. Open **Developer tools → Actions**.

## 4. Post-restart preflight

Confirm:

- Red Queen `1.0.0-rc9`;
- WNHF `1.35.0`;
- release baseline `WP-4.7.15.0`;
- phase name `Release Candidate 9`;
- runtime ready, health 100 and no Red Queen errors/warnings;
- `plants` capability resolved through `provider.core.plants`;
- `wnhf.plants_snapshot` returns 13 plants and every plant is initially `unknown`
  when no history file existed;
- 13 `sensor.wnhf_plant_care_*` entities exist;
- 13 `button.wnhf_plant_water_*` entities exist;
- every plant sensor/button pair is attached to the configured Red Queen room
  device, for example Drachenbaum Büro under `Red Queen Room (office)`.

## 5. Dry-run

```yaml
action: wnhf.execution_dry_run
data:
  action_id: plants.record_watering
  target:
    object_id: plant.eg.office.dragon_tree
  parameters: {}
```

Expected: `EXE-100`, executable, no command sent, strategy
`persistent_verified_state_event`, verification scope `state`.

## 6. Record a real watering event

Only perform this after the selected plant has actually been watered:

Press the corresponding native button, for example
`button.wnhf_plant_water_eg_office_dragon_tree`. The button routes through the
same canonical `plants.record_watering` execution contract. Do not press the button
and then also run the following service request for the same physical watering.

The equivalent direct canonical request is:

```yaml
action: wnhf.execution_execute
data:
  action_id: plants.record_watering
  target:
    object_id: plant.eg.office.dragon_tree
  parameters: {}
```

Expected: `EXE-000`, one persistent event, sensor changes to `ok`, watering count
increments once, `framework_verified: true`, `hardware_verified: false`, and
`verification_scope: state`.

The button means **record watering completed**. It does not control irrigation and
must only be pressed after a person has actually watered the plant.

## 7. Guard tests

Dry-run an unknown semantic plant ID and a request with an unexpected parameter.
Expected: `EXE-203` and `EXE-204` respectively, with no history change.

## 8. Persistence test

Restart Home Assistant completely. Confirm that the recorded plant retains
`last_watered_at`, `due_at`, status and watering count while all untouched plants
remain `unknown`.

## 9. Regression and final health

Repeat representative lighting, cover, garage, opening and notification dry-runs.
Confirm final system health 100, runtime ready and no Red Queen errors or warnings.
Record only observed results in `docs/RC9_CANDIDATE_VALIDATION.md`.
