# Red Queen 1.0.0-rc11 — Candidate Validation

Status: exact-package live qualification PASS; repository CI/hassfest pending.

## 1. Candidate identity

After installing the exact candidate package and restarting Home Assistant, confirm:

- Red Queen `1.0.0-rc11`;
- WNHF `1.37.0` / `WP-4.7.17.0`;
- phase `Release Candidate 11`;
- canonical execution API `1.0`;
- canonical execution contract `2.3-rc11`;
- 8 capabilities;
- 23 semantic actions;
- 16 canonical real actions;
- 68 Home Assistant services.

## 2. Preserve installation-owned data

Back up and preserve `/config/wnhf`. Replace only `/config/custom_components/wnhf`
with the exact consolidated candidate package. RC11 must not silently adopt or
rewrite a manual registry.

## 3. Managed configuration status

Open **Red Queen → Configure** and confirm:

- mode `managed`;
- validation `valid`;
- registry path `/config/wnhf/house/registry`;
- counts match the test registry;
- configurator menu labels are localized;
- `wnhf.configuration_snapshot` reports the ownership manifest, managed files,
  hashes and valid bundle state.

## 4. Configuration smoke tests

Use existing test objects; do not create duplicate production-like objects unless
needed.

- Room duplicate guard rejects an already configured Home Assistant Area.
- Light duplicate guard rejects an existing room/name combination.
- Existing managed light remains attached to its Red Queen room.
- Existing configured cover retains optional position/blade configuration.
- Existing opening objects retain window/sliding-door/door/garage types and options.
- Existing Plant Care entries retain interval/history/sensor metadata.

## 5. Native execution regression

Perform only safe test actions.

### Light

- toggle off/on;
- objective feedback follows;
- no duplicate command is emitted for an already satisfied state.

### Cover

- close then open;
- observe `closing` / `opening` and terminal end state;
- read-only position sensor follows objective feedback;
- blade buttons are disabled while moving;
- blade open/close works while stationary;
- no arbitrary set-position control is advertised.

### Door

With door closed:
- lock;
- unlock;
- electric door release.

With door open:
- lock/unlock are rejected with the localized closed-door guard;
- door release is unavailable/rejected;
- no command is dispatched.

### Garage

- open only from proven closed end position;
- close only from proven open end position;
- direction controls disappear/block in ambiguous intermediate state;
- when dedicated STOP is configured, STOP is available only while moving;
- STOP dispatches exactly one STOP command and does not claim a resulting position.

### Plant Care

- existing watered plant retains `last_watered_at`, `due_at` and count;
- a plant without history remains `unknown`;
- record one real test watering only when physically intended;
- optional moisture sensor reference remains configured but does not change care
  status by itself.

## 6. Restart persistence

Restart Home Assistant completely and repeat representative light, cover, door,
garage and Plant Care state checks. Entity/device/area associations must remain stable.

## 7. Runtime health

Confirm:

- Red Queen runtime ready;
- health 100;
- zero Red Queen errors;
- zero Red Queen warnings;
- no integration setup/reload exceptions;
- no invalid managed registry files.

## 8. Repository publication gates

Before publishing:

- apply the exact verified integration source to a `release/1.0.0-rc11` branch;
- update repository-level changelog/release documentation;
- run repository static verification;
- pass Home Assistant hassfest;
- review the branch diff against published RC10;
- fast-forward/merge only the verified candidate;
- tag `v1.0.0-rc11` on that exact commit;
- publish as a GitHub pre-release only after all gates pass.

## Iterative qualification already observed during RC11 development

The dedicated test installation already passed the individual managed-configuration,
light, cover, opening/access, garage STOP, Plant Care, recovery, persistence and
localized-guard tests documented in the RC11 release notes. Those results establish
functional confidence. The exact consolidated candidate package was then installed
and requalified successfully on 2026-08-22 before repository publication work.

## Exact-package live qualification result — 2026-08-22

**PASS**

The exact consolidated candidate ZIP with SHA-256
`9ad0f802d11dce56900323b1a50a1333f3d60d51e26e6522f404ceb7b6e7ce35`
was installed on the dedicated Home Assistant test system.

Observed results:

- Red Queen reported `1.0.0-rc11`;
- managed registry loaded valid with the configured room, light, cover, opening/access,
  garage and Plant Care objects;
- native impulse light execution and objective feedback passed;
- venetian-blind open/close, movement state, read-only position and blade UI guards
  passed;
- the open-door motor-lock guard rejected locking with the localized German message
  and dispatched no lock pulse;
- garage open/close and guarded intermediate-state behavior passed;
- Plant Care record-watering behavior passed;
- the final Home Assistant restart preserved the registry and test objects and
  completed normally;
- no Red Queen regression was observed during the exact-package pass.

The dedicated RC11 test Home Assistant installation was removed after this successful
qualification. Remaining publication gates are repository diff review, static CI and
Home Assistant hassfest.
