# Red Queen Release Process

## Current state

`1.0.0-rc1` is LIVE VERIFIED and frozen. The exact verified runtime source is stored under `custom_components/wnhf` in this repository preparation snapshot.

## RC soak

Run the RC in normal home operation across multiple real day/night cycles. Monitor Red Queen logs, `wnhf.system_status`, registry validation, stable state reporting and canonical execution behavior.

### Outcome

- **No RC blocker:** promote to `1.0.0` after final packaging/smoke validation.
- **RC blocker found:** fix only the blocker, create `1.0.0-rc2`, and repeat the affected regression gates plus release smoke tests.

## Promotion to 1.0.0

If RC1 requires no runtime code changes, promotion to `1.0.0` should be a release-identity/documentation change only. The runtime behavior must remain equivalent to the verified candidate and receive a final read-only smoke test.

If runtime code must change, do not promote directly to final. Create another RC first.

## Versioning after 1.0

Use semantic versioning:

- patch (`1.0.1`) for compatible bug fixes;
- minor (`1.1.0`) for compatible new features/domains;
- major (`2.0.0`) for intentionally incompatible public-contract changes.

Planned future domains are documented in `docs/ROADMAP.md`; their order is not a release promise.

## Immutable release artifacts

Never silently replace an already published release artifact. A changed artifact requires a new version/tag.
