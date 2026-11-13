# Red Queen 1.2 — Site cutover & rollback gates

**NOT A DEPLOYMENT SCRIPT.** No production change is authorized by the
existence of this checklist or by a green development CI run. Complete gates
in sequence, using local private offline artifacts and explicit operator
approval for the maintenance window.

## A. Source freeze and acceptance

- [ ] Reviewed RC commit SHA, branch ancestry, release metadata, and
      manifest/runtime/RELEASE consistency. The new package contains only
      `custom_components/red_queen`, never a parallel `wnhf` integration.
- [ ] GitHub Actions tests, hassfest, scoped HA boot, dashboard/Store restore,
      config-entry reload/unload, safe-mode and regressions passed for the
      exact package SHA selected for deployment.
- [ ] Existing installation domain/version, actual HA image digest and
      Docker `/config` bind mount checked independently.
- [ ] Fresh and **consistent** pre-cutover backup taken and restored offline.
      A running-container filesystem copy is not an acceptable substitute.
- [ ] New isolated stage created only from that restored backup and the
      exact release package, with private mode-0700 parent, SHA-256 source
      comparison, independent unmodified rollback and no path overlap with
      live `/config`.
- [ ] Exactly one old-domain config entry; expected entity/device counts,
      no ambiguous duplicate IDs, zero active legacy service references;
      dashboard and Smart Living stores preserved.
- [ ] Network/device isolation proven before any lab HA boot. No real PLC,
      covers, garage, locks, notifications or physical lights exercised by
      isolated tests.
- [ ] Remaining functionality gaps and expected unavailable-entity warnings
      separately acknowledged. A scoped boot does not certify all 51 other
      HA integrations.

## B. Production change control

- [ ] Operator explicitly approves a supervised maintenance window and has
      local/remote console plus independent recovery access.
- [ ] Both existing HA exterior-light fallback automations remain **on**
      during the *integration-domain* cutover, to preserve lighting schedules;
      do not start with Red Queen native outdoor automations enabled.
- [ ] Stop HA before changing any integration package or `.storage` registry.
      Never mutate HA live `.storage` while HA is running.
- [ ] Capture rollback path, container image digest and an unambiguous
      restore command before the first write.
- [ ] Perform atomic, reviewed staged-config replacement with an operator
      checkpoint. Do not combine 1.1 `wnhf` package/registries with 1.2
      `red_queen` package/registries or run both concurrently.

## C. Post-start acceptance (fail closed)

- [ ] Exactly one `red_queen` config entry loaded; no duplicate `wnhf`
      integration loaded. Native entity/device identities unchanged.
- [ ] Dashboard and Smart Living mode restored; Lovelace automations and
      user-authored references resolve without old `wnhf.*` service calls.
- [ ] Native lighting, RGBW color/brightness, covers, sensors, openings,
      notifications, garage and third-party integrations checked with safe,
      operator-observed actions at appropriate times. Do not remotely
      activate sensitive garage/security actions as an automated smoke test.
- [ ] Existing HA exterior-light fallbacks verified active. New Red Queen
      exterior rules still disabled; interior scenes retained.
- [ ] System logs reviewed after stabilization; unexpected error => STOP
      rollout, capture privacy-safe summary, restore prior system.

## D. Separately approved automation handover

- [ ] Exact three exterior lights and both HA automation IDs/behavior
      verified on site; note names alone are not a complete interlock.
- [ ] Document sunset behavior during away/vacation/quiet and 23:00 missed
      OFF recovery policy.
- [ ] In an attended cutover window, first disable the two known HA fallback
      automations, verify their disabled states, *then* enable two native
      Red Queen rules and verify safe behavior.
- [ ] If either step fails, disable the new Red Queen rules before
      re-enabling the original HA fallback automations.

## E. Rollback

- [ ] If gates fail, STOP HA; restore the exact backed-up 1.1 code,
      HA configuration, `.storage` records and original service references
      as one coherent unit. Do not mix half-migrated files.
- [ ] Start HA only after verifying the original `wnhf` config entry,
      original 245 entities/36 device ownership baseline and dashboard
      files against the backup, adjusting counts only if a new baseline
      was deliberately accepted.
- [ ] Verify the original two HA exterior-light automations and the physical
      controls behave correctly. Preserve logs and private evidence locally.

**Do not merge PR #6, publish stable v1.2.0 or deploy without the above
acceptance.** A release candidate can be tested without being declared stable.
