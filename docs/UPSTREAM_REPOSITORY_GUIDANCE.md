# Upstream Repository Guidance

Checked: 2026-08-10.

This repository layout was prepared against current public guidance from Home Assistant and HACS.

## Home Assistant

A standalone custom integration lives under `custom_components/<domain>/` and requires a version in its manifest. Home Assistant provides an official hassfest GitHub Action for standalone integration repositories.

References:

- https://developers.home-assistant.io/docs/creating_integration_file_structure/
- https://developers.home-assistant.io/docs/creating_integration_manifest/
- https://github.com/home-assistant/actions

## HACS (optional)

Current HACS integration repository guidance expects one integration under `custom_components/`, a root `hacs.json`, required manifest metadata (`domain`, `documentation`, `issue_tracker`, `codeowners`, `name`, `version`), and brand assets. GitHub releases are preferred but optional.

References:

- https://www.hacs.xyz/docs/publish/start/
- https://www.hacs.xyz/docs/publish/integration/
- https://www.hacs.xyz/docs/publish/action/

HACS is intentionally **not activated** in this preparation snapshot because repository URLs, codeowner, license and brand assets are not yet finalized.
