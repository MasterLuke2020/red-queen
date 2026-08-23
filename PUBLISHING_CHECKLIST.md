# Publishing Checklist

## RC11 candidate preparation

- [x] Start from the published, live-verified RC10 source.
- [x] Add managed registry ownership and transaction-safe configuration.
- [x] Add guided configuration for rooms, lights, covers, openings and Plant Care.
- [x] Add automatic semantic IDs and duplicate guards.
- [x] Add canonical guarded `garage.stop`.
- [x] Preserve existing access, cover, notification and Plant Care safety contracts.
- [x] Advance to 8 capabilities, 23 semantic actions, 16 canonical real contracts
  and 68 Home Assistant services.
- [x] Add and verify `checksums/rc11_source.sha256`.
- [x] Build the exact replaceable Home Assistant candidate package.
- [x] Complete exact-package live qualification.
- [x] Create and push `release/1.0.0-rc11`.
- [x] Confirm Home Assistant hassfest passes.

## GitHub web release flow

- [ ] Confirm the final static repository check passes.
- [ ] Review the release-branch diff against published RC10.
- [ ] Fast-forward `main` to the final RC11 release commit.
- [ ] Create annotated tag `v1.0.0-rc11` on that exact commit.
- [ ] Publish GitHub Pre-Release `v1.0.0-rc11` using
  `custom_components/wnhf/docs/RELEASE_NOTES_1.0.0-rc11.md`.
- [ ] Record final commit, tag object and release artifact checksums.

## Boundaries

- Do not rename the `wnhf` domain, existing public services, semantic IDs or
  persisted paths.
- Do not silently adopt or rewrite a manual registry.
- Do not weaken objective feedback or confirmation guards.
- Do not advertise arbitrary cover set-position or invent blade position.
- Do not infer a physical stopped garage position from STOP dispatch.
- Do not use optional plant moisture input as an RC11 watering decision.
- Keep climate deferred and HACS metadata inactive.
