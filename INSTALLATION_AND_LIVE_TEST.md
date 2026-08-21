# Red Queen 1.0.0-rc8 — Installation and live qualification

Status: static verified for WP-4.7.14.0. Reference-installation live qualification
is required before publication.

## 1. Back up the current installation

Back up these paths before replacing anything:

- `/config/custom_components/wnhf`
- `/config/wnhf/house/registry/covers.yaml`
- `/config/wnhf/house/registry/openings.yaml`
- `/config/wnhf/house/registry/notification_targets.yaml`, if present

RC8 does not require new helper scripts or automations.

## 2. Registry requirements

Every cover intended for canonical blade execution requires:

```yaml
commands:
  blades_open_entity_id: button.example_blades_open
  blades_close_entity_id: button.example_blades_close
capabilities:
  - blades_open
  - blades_close
```

Objective blade-position feedback is not required.

Every door intended for canonical electric release requires a normal state contact
plus:

```yaml
door_opener:
  enabled: true
  command:
    entity_id: button.example_door_opener
```

The state contact must provide a proven closed state before release is permitted.

## 3. Install the candidate

1. Replace `/config/custom_components/wnhf` with the packaged
   `custom_components/wnhf` directory.
2. Keep the installation-owned registry files already verified for this house.
3. Restart Home Assistant completely.
4. Open **Developer tools → Actions** for controlled tests.

## 4. Post-restart preflight

Confirm that Red Queen reports:

- Red Queen `1.0.0-rc8`;
- WNHF `1.34.0`;
- release baseline `WP-4.7.14.0`;
- phase name `Release Candidate 8`;
- runtime ready with no Red Queen setup errors;
- cover and openings capabilities resolved, available and healthy.

## 5. Cover blade dry-run

```yaml
action: wnhf.execution_dry_run
data:
  action_id: covers.blades_open
  target:
    object_id: cover.eg.bathroom_wc.main
  parameters: {}
```

Expected: `EXE-100`, executable, no command sent and technical strategy
`dispatch_scoped_blade_pulse`.

Repeat with `covers.blades_close`.

## 6. Cover blade real execution

```yaml
action: wnhf.execution_execute
data:
  action_id: covers.blades_open
  target:
    object_id: cover.eg.bathroom_wc.main
  parameters: {}
```

Expected: `EXE-000`, exactly one configured command dispatch and visible blade
movement. Repeat with `covers.blades_close`.

Successful qualification must report `framework_verified: true`,
`hardware_verified: false` and `verification_scope: dispatch`.

## 7. Door release dry-run

```yaml
action: wnhf.execution_dry_run
data:
  action_id: openings.release
  target:
    object_id: opening.eg.vestibule.door.courtyard
  parameters: {}
  confirmed: true
```

Expected: `EXE-100`, executable, no pulse sent and technical strategy
`confirmed_dispatch_scoped_momentary_pulse`.

## 8. Door release real execution

```yaml
action: wnhf.execution_execute
data:
  action_id: openings.release
  target:
    object_id: opening.eg.vestibule.door.courtyard
  parameters: {}
  confirmed: true
```

Expected: `EXE-000` and exactly one physically observable electric door-opener pulse.
Repeat for `opening.eg.vestibule.door.street`.

Successful qualification must report `framework_verified: true`,
`hardware_verified: false` and `verification_scope: dispatch`.

## 9. Guard tests

Verify without unintended commands:

- blade action while the selected cover is moving;
- blade action for an unknown semantic target;
- door release with `confirmed: false`;
- door release while the selected door contact reports open;
- door release for an unknown semantic target;
- raw `button.*` or `cover.*` provider entity used as the semantic target.

## 10. Regression and final health

Repeat representative lighting, directional cover, garage, lock/unlock and
notification dry-runs. Confirm final system health 100, runtime ready and no Red
Queen errors or warnings. Record every observed result in
`docs/RC8_CANDIDATE_VALIDATION.md`.
