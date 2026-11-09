# Red Queen 1.2 — Haus-Staging und Wiederherstellungsprobe

**Status: Entwicklungswerkzeug, keine Produktionsfreigabe.**
Stand 09.11.2026. Productive \`wnhf\` / Red Queen 1.1.0 and the two
enabled Home Assistant outdoor-light automations remain unchanged.

## Objective

Rehearse the technical \`wnhf\` → \`red_queen\` domain migration on a
**consistent, previously restored and entirely offline Home Assistant
backup**. Do not operate the productive Home Assistant container or
touch its running \`/config\` bind mount.

This is a **file-level recovery rehearsal**. A verified byte-identical
rollback copy is useful evidence, but it is NOT proof of an actual full
live-site disaster recovery and not sufficient to authorize deployment.

## Hard safety gates

- Use **only an existing, verifiably consistent Restic/DR restore** from a
  completed backup, not a live \`cp\` or \`rsync\` of the running \`/config\`.
- Never export production HA backups, \`.storage\`, credentials, PLC IPs or
  tokens to GitHub, CI artifacts, this chat or a shared directory.
- Keep the source, staging directory and independent rollback copy under
  a *private locally controlled* filesystem. Output parent folders must
  already exist, be mode \`0700\` and have sufficient free space for two
  full snapshot copies. The script refuses an existing output folder.
- Supply the actual live Home Assistant \`/config\` host-mount path as
  \`--live-config\`. The tool refuses sources and destinations that overlap
  this live mount. The user must not manually fabricate that value.
- Do not run a second Home Assistant on the staged snapshot. The backup
  contains real hardware endpoints and user tokens; first prepare a separate
  network/device-isolation test plan.
- Never merge the draft pull request or change the HACS installation during
  this procedure.

## Exact expected counts from the read-only house inventory

| Guard | Required |
| --- | --- |
| Old-domain config entries | 1 |
| Old-domain entity registry records | 245 |
| Devices with old-domain namespace identifiers | 36 |
| Legacy HA Store files | \`wnhf.dashboard\`, \`wnhf.smart_living\` |
| Old-domain entity IDs renamed | 0 |
| Original house registry YAML files changed | 0 |
| Source snapshot files changed | 0 |
| Copy-based restore verification | All files byte-identical |

If the actual newer snapshot has different entity or device counts, the
preflight **refuses**. Investigate the difference with the read-only
registry inventory; do not quietly adjust the thresholds.

## Preflight operation (ONLY after a real offline snapshot exists)

This is an **example**, not an instruction to guess a Restic repository.
Recover a completed backup according to the existing house recovery
manual. Confirm the restored source is the HA \`/config\` directory and
contains its \`.storage/core.*\` files, \`custom_components/wnhf\`,
\`configuration.yaml\` and the two legacy Stores.

Read the actual production config host mount without modifying anything:

    sudo docker inspect homeassistant \
      --format '{{range .Mounts}}{{if eq .Destination "/config"}}{{.Source}}{{end}}{{end}}'

Prepare two **private** output parent directories that are not inside the
source snapshot or live HA mount:

    sudo install -d -m 0700 /srv/admin/rq12-lab/isolated-stage
    sudo install -d -m 0700 /srv/admin/rq12-lab/independent-restore

Use a local checkout of the exact pinned, reviewed commit
\`feature/1.2.0-domain-identity-migration\` and run:

    sudo python3 tools/rq12_site_stage_preflight.py \
      --source /PATH/TO/CONSISTENT/RESTORED-HA-CONFIG \
      --stage /srv/admin/rq12-lab/isolated-stage/red-queen-12 \
      --rollback /srv/admin/rq12-lab/independent-restore/wnhf-11-restored \
      --live-config /ACTUAL/HOST/CONFIG/MOUNT \
      --package custom_components/red_queen \
      --expected-entities 245 --expected-devices 36

**Never** use \`--source\` pointing to the live directory. The
\`--stage\` and \`--rollback\` targets must not already exist.
The tool never downloads anything, starts HA, calls services, writes to
the source or changes backup repositories.

## What it actually proves

1. The offline backup contains exactly one \`wnhf\` config entry and the
   expected 245 entities and 36 old-namespace devices.
2. The production-source snapshot and its \`wnhf\` house registry are read
   without modification; all source-file SHA-256 hashes are verified again.
3. The same tested \`rq12_domain_stage.py\` migrates a copy to the new
   integration package and domain, preserving entity IDs and unique IDs.
4. The two existing HA Stores and house-registry files are byte-identical
   in the new staging copy.
5. A separate rollback copy is made from the untouched source; **all
   files** in that rollback copy are SHA-256 verified against the source.
6. A non-sensitive JSON report is written only in the staging directory,
   explicitly stating that **no HA was started and no live recovery was
   carried out**.

The test retains both confidential copies locally. They must be treated
with the same access controls as the actual production backup. No
automatic deletion is done; first follow the approved retention policy.

## What remains before a release candidate

- Review preflight JSON results and source-vs-stage reference inventories.
- Verify all real dashboard references, script calls, package YAML and
  Store data, including any user-authored dynamic templates.
- Perform a distinct HA boot and startup/config-entry reload test ONLY
  after strict network and device isolation is in place.
- Verify all physical exterior-light and Shelly RGBW mappings, seasonal
  conditions, manual pause and sunrise/sunset transitions.
- Prove **actual disaster recovery** using the documented Restic
  restore procedure, not just a byte-identical copy.
- Final 1.2.0 RC packaging, manifest and HACS compliance, then operator
  approval for a tightly controlled maintenance-window cutover.

**No production activation is authorized by a passed offline preflight.**

## Site discovery checkpoint — 2026-11-09

The operator checked the productive Home Assistant Docker bind mount and
confirmed that the HA container uses a normal host /config directory.
Scheduled daily server Restic backup, HA-to-NAS copy and the related
backup/retention/watchdog timers are present. Local recovery documents exist.

**This is NOT completed snapshot validation.** A systemd timer's presence
or last-trigger time does not prove that a Restic snapshot contains a
consistent HA configuration or can be restored. First check the real
backup service result and restore a specific completed snapshot using
the site's privately maintained, approved recovery guide.

The exact live host mount is kept in the private operator runbook and not
hardcoded as a public default. Pass the verified mount through --live-config
to enforce source/output isolation. Do not disclose Restic credentials,
private endpoints or config-entry data.
