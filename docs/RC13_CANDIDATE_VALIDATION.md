# RC13 Candidate Validation

## Current state

**FEATURE LIVE VERIFIED — RELEASE FREEZE**

- Red Queen: `1.0.0-rc13`
- WNHF: `1.39.0`
- Work-package baseline: `WP-4.7.19.0`
- Theme: **Managed Maintenance & Production Diagnostics**
- Canonical execution API: `1.0`
- Canonical real-execution contract: `2.3-rc11` (unchanged)

## Scope

RC13 adds managed read/select/update for rooms, lights, covers, openings and plants;
immutable semantic IDs during maintenance; transaction-safe enable/disable; guarded
two-step deletion; dependent-room and last-room protection; Entity/Provider
diagnostics for configured references; registry-source dashboard freshness; and
reload-safe dashboard flow completion.

Manual registries remain read-only. Canonical physical execution behavior is unchanged.

## Functional live qualification — 2026-09-17

The post-fix candidate at commit
`4f35dd96ed9254ca49cc86f0d27d5ead025c24d9` was installed from an exact 177-file
package with SHA-256
`bf43dcfb770f35e4fa93dba23b36a8d2667813459e93130f6cf174ed1bf1c7c5`.

PASS observations:

- fresh Home Assistant onboarding and managed commissioning;
- representative light, cover, window, door, garage and plant configuration;
- managed edit with stable semantic identity;
- enable/disable round trip;
- explicit two-step deletion;
- protected room deletion rejected while dependencies remained;
- diagnostics: 21 references, 21 ready, 0 findings;
- dashboard creation, registry-source freshness and update;
- `Invalid flow specified` regression reproduced, fixed and live retested;
- translated dashboard completion confirmed after frontend cache refresh;
- restart persistence and HTTP 200 after restart.

## Release-freeze gate

This freeze updates release metadata/documentation and the integration checksum
catalogue only. Because those files are part of the integration package, a new final
immutable package must be built from the freeze commit.

Before publication that exact package must pass repository verification, release-branch
CI/hassfest, clean integration replacement, Home Assistant startup, managed registry
load, dashboard update, diagnostics and restart persistence. The final package SHA is
then recorded in root-only release documentation so the qualified integration bytes
do not change afterward.
