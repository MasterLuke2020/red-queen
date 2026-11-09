# Red Queen 1.2.0-rc1 (development candidate)

Red Queen is a semantic Home Assistant framework. **Red Queen** is the product
name and `red_queen` is the technical integration domain in this candidate.
The previous installation used the technical domain `wnhf`.

**This is a development release candidate, not a production installation or a
stable release.** Do not install it over a running `wnhf` integration without
the verified offline domain migration and an independent rollback.

## Compatibility contracts

- Old Home Assistant `entity_id`, `unique_id` and config-entry IDs are
  deliberately preserved, including historical `wnhf_*` entity IDs.
  Renaming these IDs in the UI is **not** a side effect of the domain upgrade.
- Existing house registry/config files remain under the `wnhf/` data directory
  for compatibility; this is not a second installed integration.
- Existing `.storage/wnhf.dashboard`, `.storage/wnhf.smart_living` and
  any already-created Smart Lighting editor state are preserved.
- New service calls use the `red_queen.*` service domain. Old
  `wnhf.*` service calls must be migrated in YAML and Lovelace before cutover.
- RGBW scenes can select eligible Home Assistant light providers; native Red
  Queen semantic lights use their guarded canonical on/off execution.

## Outdoor lighting handover

Existing Home Assistant fallback automations stay enabled until a supervised
handover. The new Red Queen rules are opt-in and default to disabled. Known
active fallback automations block overlapping Red Queen scene execution, but
name-based detection does not cover arbitrary renamed automations.

The two existing interior RGBW scenes remain separate from the proposed
outdoor scene. No external light automation is enabled by installing 1.2.

## Acceptance status

Offline site backup staging, 245 Red Queen entity identities and 36 device
identities, rollback-copy consistency, isolated scoped Home Assistant boot,
dashboard/Smart Living storage checks and synthetic scheduler tests were
successful on 2026-11-09. The scoped boot excluded other integrations and
does not establish physical device operation or full site compatibility.

See `docs/RED_QUEEN_1_2_SITE_STAGING.md`,
`docs/RELEASE_NOTES_1.2.0-rc1.md` and
`docs/RED_QUEEN_1_2_CUTOVER_CHECKLIST.md` in the repository root.
