# RC12 Candidate Validation

## Scope

Red Queen `1.0.0-rc12` / WNHF `1.38.0` / `WP-4.7.18.0` introduces the Generated
Dashboard Foundation while retaining RC11 managed configuration and canonical safety.

## Live dashboard validation completed 2026-08-24

Reference test system observations:

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

## Safety boundary

- The generated dashboard invokes native Red Queen entities only.
- No provider entity fallback or broad HA state scanning is used for action binding.
- Physical safety guards remain in canonical/native execution.
- User/default Lovelace dashboards are not modified.
- Dashboard creation/update is explicit; restart restore is non-destructive.

## Remaining exact-candidate gate

This document records implementation live validation before final immutable package
creation. The final RC12 candidate still requires:

1. release metadata finalization;
2. LF-normalized source checksum catalogue;
3. repository verifier PASS;
4. release-branch CI/hassfest PASS;
5. exact-package clean-install + dashboard create/update/restart qualification.
