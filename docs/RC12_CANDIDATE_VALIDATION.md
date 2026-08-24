# RC12 Candidate Validation

## Scope

Red Queen `1.0.0-rc12` / WNHF `1.38.0` / `WP-4.7.18.0` introduces the Generated
Dashboard Foundation while retaining RC11 managed configuration and canonical safety.

## Dashboard implementation validation completed 2026-08-24

Reference test system observations before immutable package creation:

- Home Assistant started successfully with RC12 dashboard runtime modules.
- Reference manual registry loaded: 23 rooms, 43 registry lights, 17 covers,
  21 openings and 13 plants.
- Dashboard model correctly selected 34 controllable `toggle` lights; the remaining
  9 registry light entries were 7 reserved + 2 monitor-only objects.
- Preview resolved 168/168 expected native Red Queen entity bindings with 0 issues.
- Explicit `Dashboard erstellen` created `/red-queen` successfully.
- Overview, three floor views, room subviews, Plant Care and System/Diagnostics
  rendered successfully.
- Manual registry routing exposed Status + Dashboard without enabling semantic writes.
- Full Home Assistant restart preserved the dashboard and returned `Status: aktuell`.
- Renderer/model changes produced `Status: Aktualisierung verfügbar`; explicit update
  succeeded and returned to `Status: aktuell`.
- Floor labels rendered as Außenbereich, Erdgeschoss and Obergeschoss.
- Unavailable reference providers were represented as unavailable rather than falsely
  reporting calm/closed/off states.
- Oversized Recorder attributes on registry validation sensors were removed.

## Exact candidate qualification — PASS

The frozen final RC12 candidate package was clean-installed on a fresh dedicated Home
Assistant test instance and qualified on 2026-08-24.

Candidate identity:

- File: `red_queen_1.0.0-rc12_final_candidate.zip`
- Integration files: `174`
- SHA-256: `d1c683f56990ed14aa7e488564dad67d008fbd483ec3353ca793af56fec135d7`

Exact-package PASS evidence:

- Red Queen reported version `1.0.0-rc12` after fresh installation.
- Manual registry validation returned `valid` with 23 rooms, 43 registry lights,
  17 covers, 21 openings and 13 plants.
- Dashboard preview reported 3 floors, 23 rooms, 34 controllable lights, 17 covers,
  21 openings, 1 garage door and 13 plants.
- Native entity binding resolved `168/168` expected entities with 0 issues.
- `Dashboard erstellen` created `/red-queen` successfully.
- Overview, floor, room, Plant Care and System/Diagnostics navigation passed.
- A full container/Home Assistant restart completed cleanly (`exit code 0`).
- `/red-queen` persisted across restart without regeneration.
- Configurator reported `Status: aktuell` after restart.
- Post-restart logs contained no Red Queen dashboard error/traceback and no oversized
  validation-sensor Recorder warning.

After the initial exact-package qualification, hassfest identified the required
explicit `lovelace` manifest dependency. The dependency was added and manifest keys
were sorted per hassfest. Static repository checks and hassfest then passed, the final
package above was rebuilt from the frozen integration source, and targeted
startup/dashboard-restore/restart revalidation passed.

## Safety boundary

- The generated dashboard invokes native Red Queen entities only.
- No provider entity fallback or broad HA state scanning is used for action binding.
- Physical safety guards remain in canonical/native execution.
- User/default Lovelace dashboards are not modified.
- Dashboard creation/update is explicit; restart restore is non-destructive.
- Intentionally absent PLC/provider entities in the isolated acceptance system were
  allowed to remain unavailable and were not treated as dashboard failures.

## Remaining publication gate

1. Fast-forward `main` to the verified RC12 release commit.
2. Create annotated tag `v1.0.0-rc12` and publish the GitHub prerelease.
