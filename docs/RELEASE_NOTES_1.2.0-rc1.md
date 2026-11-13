# Red Queen 1.2.0-rc1 — release candidate notes

**Status (2026-11-13): DEVELOPMENT CANDIDATE — NOT YET RELEASED OR
APPROVED FOR PRODUCTION.** The manifest, runtime constants and RELEASE.json
identify `1.2.0-rc1` as a candidate/rc. The service contract uses the
technical Home Assistant domain `red_queen`.

## What changes

- Home Assistant technical domain becomes `red_queen` instead of `wnhf`.
  This is a breaking integration-domain change; simply copying files or
  updating through HACS without migration is unsafe.
- Existing Home Assistant config entry, device/entity registry records,
  unique IDs, and user-assigned entity IDs are preserved through an explicit
  offline migration. Historical `wnhf_*` entity IDs remain intentionally
  unchanged. The product is displayed as **Red Queen**.
- Active YAML and Lovelace service references are migrated to
  `red_queen.*`; historical hidden backup files are left untouched.
- Existing house files in `wnhf/`, `.storage/wnhf.dashboard` and
  `.storage/wnhf.smart_living` remain readable and are not renamed.
- Smart Lighting provides a scene editor, manufacturer-neutral eligible
  light sources, explicit opt-in scheduler rules, a manual ON pause guard,
  selected OFF replay, and a handover interlock for known HA fallback
  exterior-light automations.
- Native semantic light scenes use canonical on/off control. No auto
  activation, hardware commands or physical access are part of installation.

## Tests completed (site-derived, offline)

- Consistent restored backup: 3,709 files compared; independent identical
  rollback copy.
- Migrated Red Queen device identifiers: 36; entity records: 245, with
  stable original entity IDs/unique IDs/config-entry ID.
- Read-only legacy-reference gate: zero active blocking old-domain calls.
- Network-isolated scoped Home Assistant boot: Red Queen config entry and
  startup validation executed; all 245 entity identities preserved.
- Site-based dashboard and Smart Living stores unchanged; all six
  Lovelace storage files unchanged.
- Startup validation: zero structural errors; 255 `entity_unavailable`
  warnings expected from excluded integrations and network isolation.
- Outdoor scene: three canonical lights resolved; two disabled proposed
  rules; 23/23 pure-policy checks and synthetic scheduler dispatch passed.
- The full original HA configuration failed to initialize some
  network-related components under `--network none` (Zeroconf Errno 19).
  The successful scoped boot excluded 51 other config entries.
- The analytics component's isolated Zeroconf traceback and a synthetic
  `voluptuous` import-order warning remain documented; neither establishes
  a Red Queen code exception.

## Additional site-derived tests (2026-11-13)

These tests used the **unchanged fixed RC code at commit `5aaa2923`**,
before the subsequent release-contract corrections:

- Uninstrumented A/B test on private scoped lab copies:
  old / RC / RC / old = **PASS / PASS / PASS / PASS**.
  The two RC legs completed in 16 seconds each.
- Fresh cold-start tests on three independent private copies of the
  original 52-entry migrated house staging, scoped to one Red Queen entry:
  **RC / old / RC = PASS / PASS / PASS**, 16 seconds each.
- In every fresh test the startup validation reported zero structural errors,
  dashboard adapter initialized and all **245 entity identities** and
  **36 migrated Red Queen device identifiers** remained intact.
- Original full house stage remained unmodified (SHA-256 checked);
  all tests were network-isolated with no production changes or physical
  commands.
- Earlier uninstrumented RC stalls are **not reproducible under these
  controlled conditions**, but their root cause is not established.
  No full-house/hardware acceptance can be inferred.

## Release blockers / NOT proven

- Re-run all CI, unit/contract tests, synthetic HA boots and the scoped
  private-house staging smoke against the **final corrected commit/artifact**.
  Passing evidence for commit `5aaa2923` does not certify later edits.
- Prove config-entry reload/unload, preserved dashboard and Store state,
  safe-mode handling and coherent offline rollback before production.
- Review the released candidate's service/upgrade metadata and check that
  historical `wnhf` data paths and entity identifiers are retained without
  claiming the old `wnhf.*` service namespace remains available.
- Full non-Red-Queen integration availability, external API connections,
  WAGO/PLC, garage, covers, RGBW devices and physical light control are not
  validated by isolated tests.
- Approve external lighting behavior for away/vacation/quiet modes and
  opt-in missed 23:00 OFF before enabling any native rule.
- Confirm an immediately reversible maintenance-window cutover using a
  fresh consistent backup. Existing HA fallback automations must stay
  active until separately approved for handover.
- Review branch integration into `main`, tag/release strategy and update
  mechanism. GitHub draft PR #6 is not a release.

**Never publish site backups, credentials, device addresses or .storage
contents in GitHub, CI logs or tickets.**
