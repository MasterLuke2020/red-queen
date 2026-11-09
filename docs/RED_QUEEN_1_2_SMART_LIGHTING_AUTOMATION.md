# Red Queen 1.2 – Smart Lighting Automation (development)

> Status: **development feature branch only**. Not installed in production.
> The installed Red Queen 1.1.0 and its existing manual scene/messaging
> safeguards are unchanged. The manifest version remains 1.1.0 until a
> separate, tested versioned release.

## Product goal

Trigger existing Smart Living light scenes from Home Assistant's own local
clock, sunrise/sunset, or a verified binary state transition.

Primary example: **turn on selected exterior lights at sunset and turn off
those exact lights at 23:00 local time**. No polling clock is introduced and
no PLC/WAGO or DALI parameter is changed.

## Implemented in this branch

- Optional `automations:` entries in `/config/wnhf/smart_living.yaml`.
- Triggers:
  - `{type: sun, event: sunset, offset_minutes: 0}`
  - `{type: sun, event: sunrise, offset_minutes: 0}`
  - `{type: time, at: "23:00"}`
  - `{type: state, entity_id: binary_sensor.motion, to: "on"}`
  - `{type: state, entity_id: input_boolean.permission, to: "off"}`
- Sun callbacks are handled through HA's sunrise/sunset helpers, time triggers
  through the HA local-time helper, and state triggers through indexed
  `async_track_state_change_event`.
- Triggered actions `on` / `off` refer to existing scene IDs. `on` applies
  the scene's specified per-light on/off/brightness/color; `off` switches
  off **only** the selected scene light targets.
- Disabled by default, no writes or catch-up actions during startup.
- Permission check before every individual dispatch. `on` defaults to home
  only and blocked during quiet. Rules may explicitly opt in to
  `away/vacation` and `allow_quiet: true`; an unavailable quiet sensor
  always blocks scheduled **on**. Targeted **off** remains allowed.
- Only allowlisted native Smart Living source lights (currently the same
  DALI/explicit HA sources as manual scenes). No recursive Red Queen light
  proxies, no arbitrary service calls or entity IDs.
- Per-rule overlap prevention, registration/unregistration with HA entry
  lifecycle, no startup replays, bounded in-memory last-100 audit.
- Read-only HA service `wnhf.smart_automations_snapshot`; the returned
  entries differentiate accepted HA dispatch from physically verified state.
- Existing manual `wnhf.smart_scene_activate` continues to use the original
  house/quiet guard and cannot be used to bypass it.

## Example

See `configuration/smart_lighting_automation.example.yaml` for a
**disabled** sunset-on / 23:00-off pair of rules. The target entity in that
example is deliberately a placeholder; it must not be used as an actual
installation config without substitution and source verification.

The `scenes:` and `automations:` lists share the same Smart Living YAML.
Always merge examples into the existing file (do not duplicate root keys).
There is no runtime YAML reload in this first slice; HA restart is required.

## Native Red Queen Configurator (development GUI)

- Navigate **Red Queen → Configure → Smart Lighting → Scenes / Rules**.
- Available in both managed and manual registry modes.
- Scenes: create, rename, add a light, select an existing light to edit its
  values, remove light, or delete a scene with no dependent rules.
- Per-light controls: on/off, independent brightness (0–255), native RGB
  (red/green/blue) or RGBW (red/green/blue/white) channel values.
- Rules: define a source scene, ON or targeted OFF, sun/time/state trigger,
  allowed residential modes, night-time exception, disabled/enabled status;
  edit, toggle or delete with explicit confirmation.
- Saves never call physical light services. They use a separate versioned HA
  Store key `wnhf.smart_lighting_editor` and keep the original manual YAML
  file intact. Once the first GUI edit is saved, the GUI Store's scenes/rules
  take precedence over the corresponding YAML lists. Other YAML settings
  (DALI allowlist, away/quiet sensors, messaging route) remain in YAML.
- The existing `OptionsFlowWithReload` lifecycle reloads the Red Queen
  integration following a save so event subscriptions are refreshed; there
  is no full Home Assistant process restart and no missed-event replay.
- Each editor save preserves a one-version snapshot in Store for recovery.
  Recovery by GUI is a follow-up work item.
- If a stored scene source is deleted from the HA entity registry, the scene
  remains readable while its enabled automations are suspended (diagnosed
  via `wnhf.smart_automations_snapshot`); this must not interrupt core Red Queen.
- An existing light cannot accidentally be added twice: select **Edit
  existing scene light** for changing its values.
- HA native numeric/choice selectors are used at present. A custom graphical
  color-wheel widget is explicitly outside this first editor slice.

## Native Red Queen / WAGO exterior-light scene adapter (development)

A read-only Home Assistant Entity Registry inventory from the house showed
**8 enabled Red Queen lighting entities** among 9 exterior candidates. The
other exterior candidate is a disabled Tapo camera floodlight. There are
13 native DALI RGBW light entities for indoor color control.

- The original scene adapter intentionally allowed only native non-WNHF RGBW
  sources, so it could not operate the actual WAGO-powered outdoor lights.
- The new `smart_lighting_semantic.py` adapter resolves existing WNHF
  `light.*` entities via a strict `platform == wnhf`, active entry ID,
  enabled + controllable Red Queen registry object, and exact unique ID
  match to `WNHFLightEntity`. Renamed HA entity IDs remain supported.
- Scene and scheduler paths now accept both native DALI and native Red Queen
  semantic light sources, keeping their roles separate.
- Semantic lights accept **ON/OFF only**. They call
  `native_execution.async_execute_canonical` with the canonical object ID
  and `lighting.turn_on`/`lighting.turn_off` (same guarded route as the
  existing Red Queen light tiles). They never call `button.press` or
  re-enter the WNHF light proxy to trigger action recursively.
- Semantic lights reject RGB, RGBW, brightness, transition and any other
  attribute at the dispatch boundary; DALI scenes retain the existing
  validated color/brightness path.
- GUI editing of a semantic ON/OFF target stores only `{state: on/off}`.
  The generic editor still shows unused RGB/brightness fields when choosing
  a new mixed source; a dedicated type-aware source form remains a UX task.
- The existing manual RGBW whole-house-off subset remains unchanged; no
  implicit addition of semantic house lights to that subset.
- The sunset/23:00 exterior example is restricted by resident request to
  exactly **Garage Außen Up/Down**, **Straße Up/Down**, and **Hof Up/Down**.
  It must not switch on Hof Wand, Vorplatz Wand, Terrasse, Garage innen, or
  any other light. The disabled-by-default sample lives in
  `configuration/smart_lighting_real_outdoor_draft.example.yaml`.
  Important: the registry contains two plausible Straßen Up/Down entity IDs
  (`light.hof_vorplatz_red_queen_strasse_up_down` and
  `light.wnhf_strasse_up_down`). The draft retains the originally selected
  former ID only until its physical/canonical mapping is verified before
  enabling the rule. No automatic writes should occur until that is clear.
- HA CI uses synthetic registry objects plus the genuine
  `native_execution`-level dispatch path (with the final canonical action
  mocked). This is **not** an on-site test with physical feedback.

## Important safeguards and limitations

1. **Not yet customer ready.** This branch is not a 1.2 release and has not
   been installed on the production server.
2. A first native HA Options Flow GUI scene/rule editor now exists on this
   branch. It supports scene create/rename/delete, per-target add/edit/remove,
   sun/time/binary state rule create/edit/enable/disable/delete. The editor is
   **not yet production-released**; GUI ergonomics, rollback UI, and real-world
   tests remain to be completed.
3. **Recovery after missed OFF is not yet implemented.** If HA is offline at
   23:00, the off callback is missed. Add explicit persisted reconciliation
   and user-selectable policy before production rollout.
4. Manual override persistence is not yet implemented. No automatic ON
   replay occurs at restart, but a future distinct sensor/sun trigger could
   issue a new ON action after the resident manually switched a light off.
5. Only on/off state events from `binary_sensor` and `input_boolean` are
   supported in this slice. Numeric lux thresholds and more trigger types
   belong to the next step.
6. Scenes now support **registered Red Queen semantic ON/OFF light objects**
   as well as allowlisted DALI sources. Real outdoor wiring, time of sunset,
   scene membership and feedback behavior still require acceptance testing
   in the house before enabling rules.
7. A successfully accepted Home Assistant service call is **not** a
   physically confirmed output. It cannot diagnose MiBoxer controller
   peculiarities.
8. Per-scene batch actions are sequential and **not atomic**. Per-light errors
   are logged and shown in the audit. Multiple independent rules may still
   target the same source; cross-rule priority/arbiter is a follow-up.
9. Timezone and DST follow Home Assistant's configured local time, but
   edge-case transitions require staging integration tests with the target
   Home Assistant version before release.

## Verification and release guard

- Dependency-free parser/policy tests in
  `tests/test_smart_lighting_automation_logic.py`.
- Static CI, hassfest, and isolated Home Assistant synthetic boot run on
  the feature branch.
- Next required tests: real HA staging with synthetic sunset/time callbacks,
  real state transitions and force reload/unload without orphaned listeners;
  DST boundaries, missing sensors, missed off and manual override.
- Only after these pass should a guarded, rollback-capable 1.2 release be
  considered. Do not merge blindly into 1.1.0 production.

## Separate 1.2 workstreams

- Red Queen Identity & Branding: user-visible `wnhf_*` entity IDs and
  service aliases migrated with compatibility mapping and rollback.
- Integrated GUI scene editor with native light/color pickers and validation.
- Rule editor with schedules, conditions, diagnostic status and disable switch.
- New source adapter for Red Queen semantic/PLC lights to reach exterior
  lights even if not represented as native DALI RGBW sources.


## 1.2 opt-in night OFF recovery and manual ON pause (development)

The native scheduler offers two independent safeguards, disabled by default:

- \`reconcile_missed_off: true\` is accepted **only** for enabled,
  evening-local-time (\`18:00..23:59\`) \`action: off\` rules. After HA startup
  (also after integration reload), it issues a **targeted OFF only** if the
  HA sun state is explicitly \`below_horizon\` and the local clock is past
  the cutoff, or before 12:00 the next morning. It never replays a scheduled
  ON. If \`sun.sun\` is missing or unknown, no recovery is attempted. The
  option defaults to \`false\` and is preserved by GUI serialization.
- \`manual_pause_entity_id: input_boolean.red_queen_automatik_pause\` is an
  optional top-level Smart Living YAML setting. Create the toggle manually
  as a HA Helper; **ON** pauses every scheduled ON, while scheduled OFF
  remains active. Unknown/unavailable helper state blocks ON (fail-closed).
  If no helper is configured, current default behavior is preserved. This
  is an explicit manual override, *not* automatic inference from wall switch
  state changes; physical/manual override detection remains future work.

The scheduler serializes all rule dispatches and suppresses duplicate
concurrent executions of the same rule, avoiding interleaved commands to
the same PLC light. As with existing sequential per-scene dispatch, an
accepted HA call is not proof of physical state.

**No native rule is enabled merely by this code change.** If HA-native
transition automations for the same three outdoor lights are already
active, keep native Red Queen ON/OFF rules disabled until the transition
automations have been explicitly deactivated and the release is approved.
