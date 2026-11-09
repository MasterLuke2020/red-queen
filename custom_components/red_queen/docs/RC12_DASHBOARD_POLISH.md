# RC12 Dashboard Polish & Diagnostics

Work package: **WP-4.7.18.7**

This work package is based on RC12 Dashboard Live Test #1 and intentionally
polishes the already proven dashboard architecture instead of changing its
storage/lifecycle contract.

## Live-test findings addressed

- Manual semantic floor ids such as `house.eg`, `house.og` and `house.outdoor`
  no longer leak into the UI.  The deterministic fallback renders familiar
  human labels such as `Erdgeschoss`, `Obergeschoss` and `Außenbereich` when no
  Home Assistant Floor Registry metadata exists.
- Overview status cards no longer expose raw binary states such as `Ein`/`Aus`.
  Lights, openings and covers are summarized from their actual native Red Queen
  entities and explicitly count unavailable/unknown runtime states.
- The room summary no longer claims `alles ruhig` when one or more represented
  entities are `unknown` or `unavailable`.
- Plant Care state and the watering-history action are grouped into one native
  `vertical-stack` per plant, making larger plant lists easier to scan.
- The Red Queen system view uses semantic labels (`Bereit`, `Gültig`,
  `Laufzeitprüfung`, `Befunde`, etc.) instead of exposing raw HA states as the
  primary presentation.
- Validator sensor attributes are bounded so Home Assistant Recorder does not
  receive the complete validation report as state attributes.  Full validation
  reports remain available through the existing validator/service paths; the
  sensors now expose compact counts and a small issue-code sample.

## Light-count qualification

The live test reported 43 registry light objects but only 34 dashboard lights.
This is intentional and qualified:

- 34 are enabled, `toggle`-controlled and objectively state-backed.
- 7 are disabled `reserved` objects.
- 2 are `monitor_only` objects without command entities.

The dashboard model therefore continues to use `Light.controllable` and does
not surface reserved or monitor-only registry placeholders as controls.

## Non-goals

- No dashboard storage/lifecycle changes.
- No direct `.storage` manipulation.
- No custom Lovelace/HACS frontend dependency.
- No changes to Red Queen safety/guard execution paths.
- No attempt to make missing PLC/provider entities available in an isolated
  test Home Assistant instance.
