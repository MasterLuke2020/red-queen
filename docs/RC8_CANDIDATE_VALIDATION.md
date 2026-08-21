# Red Queen 1.0.0-rc8 Candidate Validation

Work package: WP-4.7.14.0 — Canonical Cover Blades / Electric Door Release
Development baseline: WNHF 1.34.0
Public candidate: Red Queen 1.0.0-rc8
Canonical execution API: 1.0
Canonical execution contract: 2.0-rc8

## Candidate intent

Promote the existing venetian-blind blade commands and configured residential
electric door openers into the canonical provider-neutral execution path without
inventing unavailable hardware feedback.

## Static acceptance

- Repository verifier passes.
- 66 Home Assistant services are present.
- 7 semantic capabilities and 20 semantic actions are declared.
- 14 canonical real-execution contracts are active.
- All 17 reference covers declare blade-open and blade-close command mappings.
- Both configured reference doors declare one electric door-opener command.
- Blade and release success are explicitly dispatch-scoped.
- Dispatch-scoped evidence cannot become hardware-verified.
- LF-normalized RC8 source checksums pass.
- Git whitespace hygiene passes.

## Controlled live qualification

### Startup and readiness

- Home Assistant starts with Red Queen `1.0.0-rc8`.
- Release phase reports `Release Candidate 8`.
- Capability `covers` is resolved, available and healthy.
- Capability `openings` is resolved, available and healthy.
- No Red Queen startup error or warning is present.

### Cover blades

Reference target: `cover.eg.office.courtyard`.

- `covers.blades_open` dry-run returned `EXE-100` without a command.
- Real blade-open execution returns `EXE-000` and the blades visibly open.
- Real blade-close execution returns `EXE-000` and the blades visibly close.
- Successful evidence is framework-verified and not hardware-verified.
- Blade execution while the cover is moving returned `EXE-203` without a blade
  pulse.

### Electric door release

Reference targets:

- `opening.eg.vestibule.door.courtyard`;
- `opening.eg.vestibule.door.street`.

- Missing confirmation returned `EXE-202` without a pulse.
- Confirmed dry-run returned `EXE-100` without a command for each door.
- Confirmed real execution returns `EXE-000` and exactly one opener pulse is heard or
  otherwise physically observed for each door.
- Both doors could be physically opened during the corresponding release pulse.
- Successful evidence is framework-verified and not hardware-verified.
- An open courtyard-door contact returned `EXE-203` without a pulse.

### Regression and final health

- The inherited RC7 lighting, directional-cover, garage, lock/unlock and notification
  contracts remained loaded and healthy.
- Final system status on 2026-08-21 was healthy and runtime ready.
- Final health score was 100 with zero Red Queen errors and warnings.
- No active or queued execution transaction remained after the tests.
- Home Assistant logs contained no Red Queen runtime error or warning. Two
  Home Assistant service-schema errors were caused by an operator-side attempt to
  pass `dry_run` to `wnhf.execution_execute`; the request was rejected before Red
  Queen execution and no hardware command was sent.

## Final result

**Red Queen 1.0.0-rc8 / WP-4.7.14.0 is LIVE VERIFIED on the reference
installation as of 2026-08-21.**
