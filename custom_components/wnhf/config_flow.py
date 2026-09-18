"""Config and options flows for safe Red Queen commissioning."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import (
    area_registry as ar,
    entity_registry as er,
    floor_registry as fr,
    selector,
)
from homeassistant.util import slugify

from .configuration import (
    CONFIGURATOR_MODE_MANAGED,
    CONFIGURATOR_MODE_MANUAL,
    RegistryConfigurationManager,
    WNHFConfigurationError,
)
from .configuration_diagnostics import (
    ConfigurationDiagnosticsReport,
    async_diagnose_configured_entities,
)
from .const import DOMAIN, PRODUCT_NAME, REGISTRY_ROOT
from .dashboard_service import (
    DashboardGenerationError,
    dashboard_generation_service,
)
from .localization import localized
from .migration_repair import (
    MigrationRepairFinding,
    MigrationRepairPreview,
    async_build_migration_repair_preview,
)

CONF_BUILDING_ID = "building_id"
CONF_BUILDING_NAME = "building_name"
CONF_AREAS = "areas"
CONF_AREA_ID = "area_id"
CONF_CONFIRM = "confirm"
CONF_ROOM_ID = "room_id"
CONF_FLOOR_ID = "floor_id"
CONF_COMMAND_ENTITY_ID = "command_entity_id"
CONF_FEEDBACK_ENTITY_ID = "feedback_entity_id"
CONF_COVER_NAME = "cover_name"
CONF_COVER_OPEN_COMMAND = "cover_open_command_entity_id"
CONF_COVER_CLOSE_COMMAND = "cover_close_command_entity_id"
CONF_COVER_OPEN_FEEDBACK = "cover_open_feedback_entity_id"
CONF_COVER_CLOSED_FEEDBACK = "cover_closed_feedback_entity_id"
CONF_COVER_OPENING_FEEDBACK = "cover_opening_feedback_entity_id"
CONF_COVER_CLOSING_FEEDBACK = "cover_closing_feedback_entity_id"
CONF_COVER_CLOSED_PERCENT_FEEDBACK = "cover_closed_percent_feedback_entity_id"
CONF_COVER_BLADES_ENABLED = "cover_blades_enabled"
CONF_COVER_BLADES_OPEN_COMMAND = "cover_blades_open_command_entity_id"
CONF_COVER_BLADES_CLOSE_COMMAND = "cover_blades_close_command_entity_id"
CONF_OPENING_NAME = "opening_name"
CONF_OPENING_STATE_ENTITY_ID = "opening_state_entity_id"
CONF_DOOR_LOCK_ENABLED = "door_lock_enabled"
CONF_DOOR_OPENER_ENABLED = "door_opener_enabled"
CONF_LOCK_FEEDBACK_ENTITY_ID = "lock_feedback_entity_id"
CONF_LOCK_COMMAND_ENTITY_ID = "lock_command_entity_id"
CONF_UNLOCK_COMMAND_ENTITY_ID = "unlock_command_entity_id"
CONF_DOOR_OPENER_COMMAND_ENTITY_ID = "door_opener_command_entity_id"
CONF_GARAGE_OPEN_FEEDBACK_ENTITY_ID = "garage_open_feedback_entity_id"
CONF_GARAGE_CLOSED_FEEDBACK_ENTITY_ID = "garage_closed_feedback_entity_id"
CONF_GARAGE_TOGGLE_COMMAND_ENTITY_ID = "garage_toggle_command_entity_id"
CONF_GARAGE_STOP_COMMAND_ENTITY_ID = "garage_stop_command_entity_id"
CONF_GARAGE_MOVEMENT_TIMEOUT_SECONDS = "garage_movement_timeout_seconds"
CONF_PLANT_NAME = "plant_name"
CONF_PLANT_SPECIES = "plant_species"
CONF_PLANT_LOCATION = "plant_location"
CONF_PLANT_WATERING_INTERVAL_DAYS = "plant_watering_interval_days"
CONF_PLANT_MOISTURE_SENSOR_ENTITY_ID = "plant_moisture_sensor_entity_id"
CONF_OBJECT_ID = "object_id"
CONF_ENABLED = "enabled"
CONF_DELETE_OBJECT = "delete_object"
CONF_PREPARE_MIGRATION = "prepare_migration"
CONF_START_REPAIR = "start_repair"
CONF_REPAIR_ID = "repair_id"
CONF_REPLACEMENT_ENTITY_ID = "replacement_entity_id"


def _manager(hass) -> RegistryConfigurationManager:
    return RegistryConfigurationManager(Path(hass.config.path(*REGISTRY_ROOT)))


def _status_placeholders(snapshot: dict[str, Any]) -> dict[str, str]:
    validation = snapshot["validation"]
    counts = validation.get("counts") or {}
    return {
        "mode": str(snapshot["mode"]),
        "registry_path": str(snapshot["registry_path"]),
        "validation": "valid" if validation.get("valid") else "invalid",
        "validation_error": str(validation.get("error") or "—"),
        **{
            key: str(counts.get(key, 0))
            for key in ("rooms", "lights", "covers", "openings", "plants")
        },
    }


def _dashboard_state_label(hass, state: str) -> str:
    """Return one localized Configurator label for a dashboard lifecycle state."""
    labels = {
        "not_created": ("nicht erstellt", "not created"),
        "ready": ("aktuell", "current"),
        "outdated": ("Aktualisierung verfügbar", "update available"),
        "detached": (
            "gespeichert, derzeit nicht eingebunden",
            "stored, currently detached",
        ),
        "recovery_mode": (
            "im Recovery-Modus nicht verfügbar",
            "unavailable in recovery mode",
        ),
    }
    de, en = labels.get(state, (state, state))
    return localized(hass, de=de, en=en)


def _dashboard_placeholders(hass, status) -> dict[str, str]:
    """Flatten dashboard generation status for localized Options Flow text."""
    counts = status.preview.model.counts
    lifecycle = status.lifecycle
    return {
        "dashboard_status": _dashboard_state_label(hass, lifecycle.state),
        "dashboard_path": f"/{lifecycle.url_path}",
        "floors": str(counts.floors),
        "rooms": str(counts.rooms),
        "lights": str(counts.lights),
        "covers": str(counts.covers),
        "openings": str(counts.openings),
        "garages": str(counts.garages),
        "plants": str(counts.plants),
        "bindings_resolved": str(status.preview.bindings.resolved_entity_count),
        "bindings_expected": str(status.preview.bindings.expected_entity_count),
        "binding_issues": str(len(status.preview.bindings.issues)),
    }



def _diagnostic_status_label(hass, status: str) -> str:
    labels = {
        "missing": ("Entity fehlt", "entity missing"),
        "disabled": ("Entity deaktiviert", "entity disabled"),
        "unavailable": ("Entity nicht verfügbar", "entity unavailable"),
        "unknown": ("Status unbekannt", "state unknown"),
        "state_missing": ("kein Laufzeitzustand", "runtime state missing"),
    }
    de, en = labels.get(status, (status, status))
    return localized(hass, de=de, en=en)


def _diagnostics_placeholders(
    hass,
    report: ConfigurationDiagnosticsReport,
) -> dict[str, str]:
    max_lines = 25
    lines: list[str] = []
    for issue in report.issues[:max_lines]:
        platform = issue.platform or "—"
        lines.append(
            f"- {issue.object_name} · {issue.role} · "
            f"{_diagnostic_status_label(hass, issue.status)} · "
            f"{issue.entity_id} · Provider/Integration: {platform}"
        )
    if len(report.issues) > max_lines:
        remaining = len(report.issues) - max_lines
        lines.append(
            localized(
                hass,
                de=f"- … {remaining} weitere Befunde",
                en=f"- … {remaining} more findings",
            )
        )
    if not lines:
        lines.append(
            localized(
                hass,
                de="- Keine Entity-/Provider-Probleme gefunden.",
                en="- No entity/provider problems found.",
            )
        )
    return {
        "references_total": str(report.total_references),
        "references_ready": str(report.ready_references),
        "problems": str(report.problem_count),
        "missing": str(report.missing_references),
        "disabled": str(report.disabled_references),
        "unavailable": str(report.unavailable_references),
        "unknown": str(report.unknown_references),
        "state_missing": str(report.state_missing_references),
        "skipped_disabled_objects": str(report.skipped_disabled_objects),
        "details": "\n".join(lines),
    }


def _migration_finding_label(hass, finding: MigrationRepairFinding) -> str:
    labels = {
        "missing_registry_file": ("Registry-Datei fehlt", "registry file missing"),
        "invalid_registry_document": ("Registry-Datei ungültig", "invalid registry document"),
        "invalid_root_list": ("Registry-Liste ungültig", "invalid registry list"),
        "invalid_object_entry": ("Objekteintrag ungültig", "invalid object entry"),
        "missing_object_id": ("Semantische ID fehlt", "semantic ID missing"),
        "duplicate_semantic_id": ("Doppelte semantische ID", "duplicate semantic ID"),
        "incomplete_object": ("Objekt unvollständig", "incomplete object"),
        "orphan_room_reference": ("Raumreferenz verwaist", "orphan room reference"),
        "registry_validation_error": ("Registry-Validierung fehlgeschlagen", "registry validation failed"),
        "invalid_ha_area": ("Home-Assistant-Bereich ungültig", "invalid Home Assistant area"),
        "invalid_ha_floor": ("Home-Assistant-Etage ungültig", "invalid Home Assistant floor"),
        "area_floor_mismatch": ("Bereich/Etage widersprüchlich", "area/floor mismatch"),
        "managed_maintenance_limited": (
            "Nur eingeschränkt über Managed Maintenance bearbeitbar",
            "limited managed-maintenance support",
        ),
        "entity_missing": ("Entity fehlt", "entity missing"),
        "entity_disabled": ("Entity deaktiviert", "entity disabled"),
        "entity_unavailable": ("Entity nicht verfügbar", "entity unavailable"),
        "entity_unknown": ("Entity-Status unbekannt", "entity state unknown"),
        "entity_state_missing": ("Entity ohne Laufzeitzustand", "entity runtime state missing"),
        "already_managed": ("Registry bereits verwaltet", "registry already managed"),
        "ownership_marker_conflict": (
            "Vorhandener Ownership-Marker blockiert die Übernahme",
            "existing ownership marker blocks adoption",
        ),
    }
    de, en = labels.get(finding.code, (finding.code, finding.code))
    return localized(hass, de=de, en=en)


def _migration_severity_label(hass, severity: str) -> str:
    labels = {
        "blocker": ("BLOCKER", "BLOCKER"),
        "warning": ("Warnung", "Warning"),
        "info": ("Hinweis", "Info"),
    }
    de, en = labels.get(severity, (severity, severity))
    return localized(hass, de=de, en=en)


def _migration_repair_placeholders(
    hass,
    preview: MigrationRepairPreview,
) -> dict[str, str]:
    max_lines = 30
    lines: list[str] = []
    for finding in preview.findings[:max_lines]:
        subject = "/".join(
            value for value in (finding.object_type, finding.object_id) if value
        ) or "Registry"
        context_parts = [
            value for value in (finding.field, finding.value, finding.detail) if value
        ]
        context = " · ".join(context_parts)
        suffix = f" · {context}" if context else ""
        lines.append(
            f"- {_migration_severity_label(hass, finding.severity)} · "
            f"{_migration_finding_label(hass, finding)} · {subject}{suffix}"
        )

    if len(preview.findings) > max_lines:
        remaining = len(preview.findings) - max_lines
        lines.append(
            localized(
                hass,
                de=f"- … {remaining} weitere Befunde",
                en=f"- … {remaining} more findings",
            )
        )

    if not lines:
        lines.append(
            localized(
                hass,
                de="- Keine Migrations-/Reparaturprobleme gefunden.",
                en="- No migration/repair problems found.",
            )
        )

    def yes_no(value: bool) -> str:
        return localized(
            hass,
            de="ja" if value else "nein",
            en="yes" if value else "no",
        )

    return {
        "mode": preview.mode,
        "source_valid": yes_no(preview.source_valid),
        "migration_candidate": yes_no(preview.migration_candidate),
        "migration_eligible": yes_no(preview.migration_eligible),
        "write_performed": yes_no(preview.write_performed),
        "objects_total": str(preview.total_objects),
        "blockers": str(preview.blocker_count),
        "warnings": str(preview.warning_count),
        "infos": str(preview.info_count),
        "entity_total": str(preview.entity_references_total),
        "entity_ready": str(preview.entity_references_ready),
        "proposed_files": ", ".join(preview.proposed_managed_files),
        "source_sha256": preview.source_sha256,
        "details": "\n".join(lines),
    }


def _migration_confirm_placeholders(
    preview: MigrationRepairPreview,
) -> dict[str, str]:
    return {
        "source_sha256": preview.source_sha256,
        "objects_total": str(preview.total_objects),
        "warnings": str(preview.warning_count),
        "proposed_files": ", ".join(preview.proposed_managed_files),
    }


_REPAIRABLE_FINDING_CODES = frozenset(
    {
        "entity_missing",
        "entity_disabled",
        "invalid_ha_area",
        "invalid_ha_floor",
        "area_floor_mismatch",
    }
)


def _repairable_findings(
    preview: MigrationRepairPreview,
) -> tuple[MigrationRepairFinding, ...]:
    if preview.mode != CONFIGURATOR_MODE_MANAGED:
        return ()
    return tuple(
        finding
        for finding in preview.findings
        if finding.code in _REPAIRABLE_FINDING_CODES
        and finding.object_type
        and finding.object_id
    )


def _repair_key(finding: MigrationRepairFinding) -> str:
    return "|".join(
        (
            finding.code,
            finding.object_type or "",
            finding.object_id or "",
            finding.field or "",
            finding.value or "",
        )
    )


def _repair_options(
    hass,
    preview: MigrationRepairPreview,
) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    for finding in _repairable_findings(preview):
        subject = f"{finding.object_type}/{finding.object_id}"
        value = f" · {finding.value}" if finding.value else ""
        options.append(
            {
                "value": _repair_key(finding),
                "label": (
                    f"{_migration_finding_label(hass, finding)} · "
                    f"{subject}{value}"
                ),
            }
        )
    return options


def _repair_find(
    preview: MigrationRepairPreview,
    repair_id: str,
) -> MigrationRepairFinding | None:
    return next(
        (
            finding
            for finding in _repairable_findings(preview)
            if _repair_key(finding) == repair_id
        ),
        None,
    )


def _repair_entity_placeholders(
    finding: MigrationRepairFinding,
) -> dict[str, str]:
    return {
        "object_id": str(finding.object_id or "—"),
        "role": str(finding.field or "—"),
        "old_entity_id": str(finding.value or "—"),
    }


def _repair_room_placeholders(
    hass,
    finding: MigrationRepairFinding,
) -> dict[str, str]:
    return {
        "object_id": str(finding.object_id or "—"),
        "finding": _migration_finding_label(hass, finding),
        "old_value": str(finding.value or "—"),
    }


def _semantic_floor_id(name: str | None) -> str:
    """Return the stable semantic floor segment used by generated object IDs."""
    return slugify(name or "unassigned") or "unassigned"


def _semantic_room_id(*, floor_name: str | None, area_name: str) -> str:
    """Build one stable semantic room ID from HA floor and area names."""
    return (
        f"house.{_semantic_floor_id(floor_name)}."
        f"{slugify(area_name) or 'room'}"
    )


def _semantic_light_id(*, room_id: str, light_name: str) -> str:
    """Build one stable semantic light ID from room identity and light name."""
    room_suffix = room_id.removeprefix("house.")
    if not room_suffix:
        room_suffix = slugify(room_id) or "room"
    return f"light.{room_suffix}.{slugify(light_name) or 'light'}"


def _semantic_cover_id(*, room_id: str, cover_name: str) -> str:
    """Build one stable semantic cover ID from room identity and cover name."""
    room_suffix = room_id.removeprefix("house.")
    if not room_suffix:
        room_suffix = slugify(room_id) or "room"
    return f"cover.{room_suffix}.{slugify(cover_name) or 'cover'}"

def _semantic_opening_id(*, room_id: str, opening_name: str) -> str:
    """Build one stable semantic opening ID from room identity and opening name."""
    room_suffix = room_id.removeprefix("house.")
    if not room_suffix:
        room_suffix = slugify(room_id) or "room"
    return f"opening.{room_suffix}.{slugify(opening_name) or 'opening'}"


def _semantic_plant_id(*, room_id: str, plant_name: str) -> str:
    """Build one stable semantic plant ID from room identity and plant name."""
    room_suffix = room_id.removeprefix("house.")
    if not room_suffix:
        room_suffix = slugify(room_id) or "room"
    return f"plant.{room_suffix}.{slugify(plant_name) or 'plant'}"


def _opening_state_entry(
    *,
    room_id: str,
    name: str,
    opening_type: str,
    state_entity_id: str,
) -> dict[str, Any]:
    """Build one binary-sensor-backed opening draft."""
    return {
        "id": _semantic_opening_id(room_id=room_id, opening_name=name),
        "name": name,
        "room": room_id,
        "type": opening_type,
        "enabled": True,
        "state": {
            "entity_id": state_entity_id,
            "open_states": ["on"],
        },
    }


def _room_draft(
    *,
    area: Any,
    floor: Any | None,
    ha_floor_id: str | None,
) -> dict[str, Any]:
    """Build one managed semantic room draft from HA registry entries."""
    floor_name = floor.name if floor is not None else None
    return {
        "id": _semantic_room_id(floor_name=floor_name, area_name=area.name),
        "name": area.name,
        "floor": _semantic_floor_id(floor_name),
        "type": "room",
        "enabled": True,
        "tags": [],
        "aliases": [],
        # Source metadata is intentionally optional for the production loader.
        # Keeping it in managed YAML lets later configurator revisions retain a
        # deterministic link to the originating Home Assistant registries.
        "ha_area_id": area.id,
        "ha_floor_id": ha_floor_id,
    }


def _selected_area_rooms(hass, area_ids: list[str]) -> list[dict[str, Any]]:
    """Build deterministic semantic room drafts from selected HA areas."""
    areas = ar.async_get(hass)
    floors = fr.async_get(hass)
    result: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    for area_id in area_ids:
        area = areas.async_get_area(area_id)
        if area is None:
            continue
        floor = floors.async_get_floor(area.floor_id) if area.floor_id else None
        room = _room_draft(
            area=area,
            floor=floor,
            ha_floor_id=area.floor_id,
        )
        base = room["id"]
        object_id = base
        suffix = 2
        while object_id in used_ids:
            object_id = f"{base}_{suffix}"
            suffix += 1
        room["id"] = object_id
        used_ids.add(object_id)
        result.append(room)
    return result


def _base_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_BUILDING_ID,
                default=defaults.get(CONF_BUILDING_ID, "house"),
            ): str,
            vol.Required(
                CONF_BUILDING_NAME,
                default=defaults.get(CONF_BUILDING_NAME, "Red Queen House"),
            ): str,
            vol.Required(CONF_AREAS): selector.AreaSelector(
                selector.AreaSelectorConfig(multiple=True)
            ),
        }
    )


def _review_placeholders(pending: dict[str, Any]) -> dict[str, str]:
    return {
        "building_id": pending[CONF_BUILDING_ID],
        "building_name": pending[CONF_BUILDING_NAME],
        "room_count": str(len(pending["rooms"])),
        "rooms": ", ".join(
            f"{room['name']} ({room['id']})" for room in pending["rooms"]
        ),
    }


class WNHFConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create the singleton entry and commission an empty installation."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        self._pending_base: dict[str, Any] | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return WNHFOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        manager = _manager(self.hass)
        snapshot = await self.hass.async_add_executor_job(manager.snapshot)
        if snapshot["mode"] == "uninitialized":
            return await self.async_step_commissioning()
        if user_input is not None:
            return self.async_create_entry(
                title=PRODUCT_NAME,
                data={"registry_mode": snapshot["mode"]},
            )
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders=_status_placeholders(snapshot),
        )

    async def async_step_commissioning(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            rooms = _selected_area_rooms(self.hass, list(user_input[CONF_AREAS]))
            if not rooms:
                errors["base"] = "invalid_commissioning_selection"
            else:
                self._pending_base = {
                    CONF_BUILDING_ID: user_input[CONF_BUILDING_ID].strip(),
                    CONF_BUILDING_NAME: user_input[CONF_BUILDING_NAME].strip(),
                    "rooms": rooms,
                }
                return await self.async_step_review()
        return self.async_show_form(
            step_id="commissioning",
            data_schema=_base_schema(user_input),
            errors=errors,
        )

    async def async_step_review(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._pending_base is None:
            return self.async_abort(reason="commissioning_state_lost")
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input[CONF_CONFIRM]:
                errors["base"] = "confirmation_required"
            else:
                try:
                    result = await self.hass.async_add_executor_job(
                        partial(
                            _manager(self.hass).create_managed_base,
                            building_id=self._pending_base[CONF_BUILDING_ID],
                            building_name=self._pending_base[CONF_BUILDING_NAME],
                            rooms=self._pending_base["rooms"],
                        )
                    )
                except WNHFConfigurationError:
                    errors["base"] = "cannot_write_registry"
                else:
                    return self.async_create_entry(
                        title=PRODUCT_NAME,
                        data={
                            "registry_mode": CONFIGURATOR_MODE_MANAGED,
                            "commissioning_action": result.action,
                        },
                    )
        return self.async_show_form(
            step_id="review",
            data_schema=vol.Schema(
                {vol.Required(CONF_CONFIRM, default=False): bool}
            ),
            errors=errors,
            description_placeholders=_review_placeholders(self._pending_base),
        )

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        snapshot = await self.hass.async_add_executor_job(_manager(self.hass).snapshot)
        return self.async_create_entry(
            title=PRODUCT_NAME,
            data={"registry_mode": snapshot["mode"]},
        )


class WNHFOptionsFlow(config_entries.OptionsFlowWithReload):
    """Inspect, extend and safely maintain configurator-managed registries."""

    def __init__(self) -> None:
        self._pending_base: dict[str, Any] | None = None
        self._pending_cover: dict[str, Any] | None = None
        self._pending_opening: dict[str, Any] | None = None
        self._pending_door_opener_enabled = False
        self._pending_object_type: str | None = None
        self._pending_object: dict[str, Any] | None = None
        self._pending_migration_sha256: str | None = None
        self._pending_repair: dict[str, Any] | None = None


    def _init_placeholders(self, snapshot: dict[str, Any]) -> dict[str, str]:
        placeholders = _status_placeholders(snapshot)
        refresh_recommended = bool(
            self.config_entry.options.get("dashboard_refresh_recommended", False)
        )
        placeholders["dashboard_hint"] = localized(
            self.hass,
            de=(
                "Konfiguration geändert – Dashboard-Status prüfen."
                if refresh_recommended
                else "Keine ausstehende Konfigurator-Änderung markiert."
            ),
            en=(
                "Configuration changed – check dashboard status."
                if refresh_recommended
                else "No pending Configurator change is marked."
            ),
        )
        return placeholders

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        snapshot = await self.hass.async_add_executor_job(_manager(self.hass).snapshot)
        if snapshot["mode"] == "uninitialized":
            return await self.async_step_create_base()
        if snapshot["mode"] == CONFIGURATOR_MODE_MANUAL:
            return self.async_show_menu(
                step_id="init",
                menu_options=[
                    "status",
                    "diagnostics",
                    "migration_repair",
                    "dashboard",
                ],
                description_placeholders=self._init_placeholders(snapshot),
            )
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "status",
                "diagnostics",
                "migration_repair",
                "add_room",
                "add_light",
                "add_cover",
                "add_opening",
                "add_plant",
                "manage",
                "dashboard",
            ],
            description_placeholders=self._init_placeholders(snapshot),
        )


    async def async_step_diagnostics(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Inspect configured provider/entity references without mutation."""
        if user_input is not None:
            return self.async_create_entry(title="", data=self.config_entry.options)

        manager = _manager(self.hass)
        report = await async_diagnose_configured_entities(
            self.hass,
            manager.registry_dir,
        )
        return self.async_show_form(
            step_id="diagnostics",
            data_schema=vol.Schema({}),
            description_placeholders=_diagnostics_placeholders(
                self.hass,
                report,
            ),
        )

    async def async_step_migration_repair(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        manager = _manager(self.hass)
        preview = await async_build_migration_repair_preview(
            self.hass,
            manager.registry_dir,
        )

        if user_input is not None:
            if user_input.get(CONF_START_REPAIR, False):
                if not _repairable_findings(preview):
                    return self.async_abort(reason="repair_not_available")
                return await self.async_step_repair_select()

            if not user_input.get(CONF_PREPARE_MIGRATION, False):
                return self.async_abort(reason="migration_repair_preview_closed")
            if not preview.migration_eligible:
                return self.async_abort(reason="migration_not_eligible")
            self._pending_migration_sha256 = preview.source_sha256
            return await self.async_step_migration_repair_confirm()

        schema: dict[Any, Any] = {}
        if preview.migration_eligible:
            schema[vol.Required(CONF_PREPARE_MIGRATION, default=False)] = bool
        if _repairable_findings(preview):
            schema[vol.Required(CONF_START_REPAIR, default=False)] = bool

        return self.async_show_form(
            step_id="migration_repair",
            data_schema=vol.Schema(schema),
            description_placeholders=_migration_repair_placeholders(
                self.hass,
                preview,
            ),
        )

    async def async_step_migration_repair_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        expected_sha256 = self._pending_migration_sha256
        if expected_sha256 is None:
            return self.async_abort(reason="migration_state_lost")

        manager = _manager(self.hass)
        preview = await async_build_migration_repair_preview(
            self.hass,
            manager.registry_dir,
        )
        if (
            not preview.migration_eligible
            or preview.source_sha256 != expected_sha256
        ):
            self._pending_migration_sha256 = None
            return self.async_abort(reason="migration_source_changed")

        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_CONFIRM, False):
                errors["base"] = "confirmation_required"
            else:
                try:
                    result = await self.hass.async_add_executor_job(
                        partial(
                            manager.adopt_manual_registry,
                            expected_source_sha256=expected_sha256,
                        )
                    )
                except WNHFConfigurationError as err:
                    message = str(err)
                    if "source changed" in message:
                        errors["base"] = "migration_source_changed"
                    elif "ownership marker" in message:
                        errors["base"] = "migration_ownership_conflict"
                    else:
                        errors["base"] = "migration_apply_failed"
                else:
                    self._pending_migration_sha256 = None
                    return self._finish_migration(
                        result=result,
                        source_sha256=expected_sha256,
                    )

        return self.async_show_form(
            step_id="migration_repair_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_CONFIRM, default=False): bool}
            ),
            errors=errors,
            description_placeholders=_migration_confirm_placeholders(preview),
        )

    async def async_step_repair_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        manager = _manager(self.hass)
        preview = await async_build_migration_repair_preview(
            self.hass,
            manager.registry_dir,
        )
        options = _repair_options(self.hass, preview)
        if not options:
            return self.async_abort(reason="repair_not_available")

        errors: dict[str, str] = {}
        if user_input is not None:
            repair_id = str(user_input[CONF_REPAIR_ID])
            finding = _repair_find(preview, repair_id)
            if finding is None:
                errors[CONF_REPAIR_ID] = "repair_issue_changed"
            else:
                self._pending_repair = {
                    "source_sha256": preview.source_sha256,
                    "repair_id": repair_id,
                    "finding": finding,
                }
                if finding.code in {"entity_missing", "entity_disabled"}:
                    return await self.async_step_repair_entity()
                return await self.async_step_repair_room_link()

        return self.async_show_form(
            step_id="repair_select",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_REPAIR_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def _async_current_pending_repair(
        self,
    ) -> tuple[MigrationRepairPreview, MigrationRepairFinding] | None:
        pending = self._pending_repair
        if pending is None:
            return None
        manager = _manager(self.hass)
        preview = await async_build_migration_repair_preview(
            self.hass,
            manager.registry_dir,
        )
        if preview.source_sha256 != pending["source_sha256"]:
            return None
        finding = _repair_find(preview, str(pending["repair_id"]))
        if finding is None:
            return None
        return preview, finding

    async def async_step_repair_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        current = await self._async_current_pending_repair()
        if current is None:
            self._pending_repair = None
            return self.async_abort(reason="repair_source_changed")
        preview, finding = current

        old_entity_id = str(finding.value or "")
        domain = old_entity_id.partition(".")[0]
        if not domain:
            self._pending_repair = None
            return self.async_abort(reason="repair_not_supported")

        errors: dict[str, str] = {}
        if user_input is not None:
            replacement_entity_id = str(
                user_input[CONF_REPLACEMENT_ENTITY_ID]
            )
            if not user_input.get(CONF_CONFIRM, False):
                errors["base"] = "confirmation_required"
            elif replacement_entity_id == old_entity_id:
                errors[CONF_REPLACEMENT_ENTITY_ID] = "repair_same_entity"
            else:
                entity_registry = er.async_get(self.hass)
                entry = entity_registry.async_get(replacement_entity_id)
                state = self.hass.states.get(replacement_entity_id)
                if entry is None and state is None:
                    errors[CONF_REPLACEMENT_ENTITY_ID] = (
                        "repair_replacement_missing"
                    )
                elif entry is not None and entry.disabled_by is not None:
                    errors[CONF_REPLACEMENT_ENTITY_ID] = (
                        "repair_replacement_disabled"
                    )
                else:
                    try:
                        result = await self.hass.async_add_executor_job(
                            partial(
                                _manager(self.hass).repair_entity_reference,
                                object_type=str(finding.object_type),
                                object_id=str(finding.object_id),
                                role=str(finding.field),
                                expected_entity_id=old_entity_id,
                                replacement_entity_id=replacement_entity_id,
                                expected_source_sha256=preview.source_sha256,
                            )
                        )
                    except WNHFConfigurationError as err:
                        if "source changed" in str(err):
                            errors["base"] = "repair_source_changed"
                        else:
                            errors["base"] = "repair_apply_failed"
                    else:
                        self._pending_repair = None
                        return self._finish_repair(result)

        return self.async_show_form(
            step_id="repair_entity",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_REPLACEMENT_ENTITY_ID
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain=domain)
                    ),
                    vol.Required(CONF_CONFIRM, default=False): bool,
                }
            ),
            errors=errors,
            description_placeholders=_repair_entity_placeholders(finding),
        )

    async def async_step_repair_room_link(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        current = await self._async_current_pending_repair()
        if current is None:
            self._pending_repair = None
            return self.async_abort(reason="repair_source_changed")
        preview, finding = current

        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_CONFIRM, False):
                errors["base"] = "confirmation_required"
            else:
                area_id = str(user_input[CONF_AREA_ID])
                areas = ar.async_get(self.hass)
                area = areas.async_get_area(area_id)
                if area is None:
                    errors[CONF_AREA_ID] = "invalid_area"
                else:
                    try:
                        result = await self.hass.async_add_executor_job(
                            partial(
                                _manager(self.hass).repair_room_ha_link,
                                object_id=str(finding.object_id),
                                ha_area_id=area.id,
                                ha_floor_id=area.floor_id,
                                expected_source_sha256=preview.source_sha256,
                            )
                        )
                    except WNHFConfigurationError as err:
                        if "source changed" in str(err):
                            errors["base"] = "repair_source_changed"
                        else:
                            errors["base"] = "repair_apply_failed"
                    else:
                        self._pending_repair = None
                        return self._finish_repair(result)

        return self.async_show_form(
            step_id="repair_room_link",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AREA_ID): selector.AreaSelector(
                        selector.AreaSelectorConfig(multiple=False)
                    ),
                    vol.Required(CONF_CONFIRM, default=False): bool,
                }
            ),
            errors=errors,
            description_placeholders=_repair_room_placeholders(
                self.hass,
                finding,
            ),
        )

    async def async_step_status(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        snapshot = await self.hass.async_add_executor_job(_manager(self.hass).snapshot)
        if user_input is not None:
            return self.async_create_entry(title="", data=self.config_entry.options)
        return self.async_show_form(
            step_id="status",
            data_schema=vol.Schema({}),
            description_placeholders=_status_placeholders(snapshot),
        )

    async def async_step_create_base(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            rooms = _selected_area_rooms(self.hass, list(user_input[CONF_AREAS]))
            if not rooms:
                errors["base"] = "invalid_commissioning_selection"
            else:
                self._pending_base = {
                    CONF_BUILDING_ID: user_input[CONF_BUILDING_ID].strip(),
                    CONF_BUILDING_NAME: user_input[CONF_BUILDING_NAME].strip(),
                    "rooms": rooms,
                }
                return await self.async_step_create_base_review()
        return self.async_show_form(
            step_id="create_base",
            data_schema=_base_schema(user_input),
            errors=errors,
        )

    async def async_step_create_base_review(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if self._pending_base is None:
            return self.async_abort(reason="commissioning_state_lost")
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input[CONF_CONFIRM]:
                errors["base"] = "confirmation_required"
            else:
                try:
                    result = await self.hass.async_add_executor_job(
                        partial(
                            _manager(self.hass).create_managed_base,
                            building_id=self._pending_base[CONF_BUILDING_ID],
                            building_name=self._pending_base[CONF_BUILDING_NAME],
                            rooms=self._pending_base["rooms"],
                        )
                    )
                except WNHFConfigurationError:
                    errors["base"] = "cannot_write_registry"
                else:
                    return self._finish(result.action)
        return self.async_show_form(
            step_id="create_base_review",
            data_schema=vol.Schema(
                {vol.Required(CONF_CONFIRM, default=False): bool}
            ),
            errors=errors,
            description_placeholders=_review_placeholders(self._pending_base),
        )

    async def async_step_add_room(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a room from HA Area/Floor registries with an automatic semantic ID."""
        errors: dict[str, str] = {}
        if user_input is not None:
            areas = ar.async_get(self.hass)
            floors = fr.async_get(self.hass)
            area = areas.async_get_area(user_input[CONF_AREA_ID])
            selected_floor_id = user_input.get(CONF_FLOOR_ID)

            if area is None:
                errors[CONF_AREA_ID] = "invalid_area"
            else:
                # Normally the area's existing floor wins automatically. An explicit
                # floor is useful for HA areas that do not yet belong to a floor, but
                # it may never contradict an existing HA floor assignment.
                if (
                    selected_floor_id is not None
                    and area.floor_id is not None
                    and selected_floor_id != area.floor_id
                ):
                    errors[CONF_FLOOR_ID] = "area_floor_mismatch"
                else:
                    effective_floor_id = selected_floor_id or area.floor_id
                    floor = (
                        floors.async_get_floor(effective_floor_id)
                        if effective_floor_id
                        else None
                    )
                    if effective_floor_id is not None and floor is None:
                        errors[CONF_FLOOR_ID] = "invalid_floor"
                    else:
                        room = _room_draft(
                            area=area,
                            floor=floor,
                            ha_floor_id=effective_floor_id,
                        )
                        try:
                            result = await self.hass.async_add_executor_job(
                                _manager(self.hass).add_room,
                                room,
                            )
                        except WNHFConfigurationError as err:
                            if "Semantic object ID already exists" in str(err):
                                errors[CONF_AREA_ID] = "room_already_configured"
                            else:
                                errors["base"] = "cannot_apply_object"
                        else:
                            return self._finish(result.action)

        return self.async_show_form(
            step_id="add_room",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_AREA_ID): selector.AreaSelector(
                        selector.AreaSelectorConfig(multiple=False)
                    ),
                    vol.Optional(CONF_FLOOR_ID): selector.FloorSelector(
                        selector.FloorSelectorConfig(multiple=False)
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_add_light(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add one impulse light with an automatic semantic ID."""
        manager = _manager(self.hass)
        try:
            room_options = await self.hass.async_add_executor_job(manager.room_options)
        except WNHFConfigurationError:
            return self.async_abort(reason="no_rooms_configured")
        if not room_options:
            return self.async_abort(reason="no_rooms_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input["name"].strip()
            if not name:
                errors["name"] = "name_required"
            else:
                room_id = user_input[CONF_ROOM_ID]
                light = {
                    "id": _semantic_light_id(room_id=room_id, light_name=name),
                    "name": name,
                    "room": room_id,
                    "enabled": True,
                    "control_mode": "toggle",
                    "command": {"entity_id": user_input[CONF_COMMAND_ENTITY_ID]},
                    "state": {"entity_id": user_input[CONF_FEEDBACK_ENTITY_ID]},
                }
                try:
                    result = await self.hass.async_add_executor_job(
                        manager.add_light,
                        light,
                    )
                except WNHFConfigurationError as err:
                    if "Semantic object ID already exists" in str(err):
                        errors["name"] = "light_already_configured"
                    else:
                        errors["base"] = "cannot_apply_object"
                else:
                    return self._finish(result.action)

        return self.async_show_form(
            step_id="add_light",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required(CONF_ROOM_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=room_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_COMMAND_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                    vol.Required(CONF_FEEDBACK_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_add_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add one venetian blind with objective direction feedback."""
        manager = _manager(self.hass)
        try:
            room_options = await self.hass.async_add_executor_job(manager.room_options)
        except WNHFConfigurationError:
            return self.async_abort(reason="no_rooms_configured")
        if not room_options:
            return self.async_abort(reason="no_rooms_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_COVER_NAME].strip()
            if not name:
                errors[CONF_COVER_NAME] = "name_required"
            else:
                room_id = user_input[CONF_ROOM_ID]
                cover = {
                    "id": _semantic_cover_id(room_id=room_id, cover_name=name),
                    "name": name,
                    "room": room_id,
                    "type": "venetian_blind",
                    "enabled": True,
                    "commands": {
                        "open_entity_id": user_input[CONF_COVER_OPEN_COMMAND],
                        "close_entity_id": user_input[CONF_COVER_CLOSE_COMMAND],
                    },
                    "feedback": {
                        "open_entity_id": user_input[CONF_COVER_OPEN_FEEDBACK],
                        "closed_entity_id": user_input[CONF_COVER_CLOSED_FEEDBACK],
                        "opening_entity_id": user_input[CONF_COVER_OPENING_FEEDBACK],
                        "closing_entity_id": user_input[CONF_COVER_CLOSING_FEEDBACK],
                    },
                    "capabilities": ["open", "close"],
                }
                closed_percent = user_input.get(CONF_COVER_CLOSED_PERCENT_FEEDBACK)
                if closed_percent:
                    cover["feedback"]["closed_percent_entity_id"] = closed_percent

                if user_input.get(CONF_COVER_BLADES_ENABLED, False):
                    self._pending_cover = cover
                    return await self.async_step_add_cover_blades()

                try:
                    result = await self.hass.async_add_executor_job(
                        manager.add_cover,
                        cover,
                    )
                except WNHFConfigurationError as err:
                    if "Semantic object ID already exists" in str(err):
                        errors[CONF_COVER_NAME] = "cover_already_configured"
                    else:
                        errors["base"] = "cannot_apply_object"
                else:
                    return self._finish(result.action)

        return self.async_show_form(
            step_id="add_cover",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COVER_NAME): str,
                    vol.Required(CONF_ROOM_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=room_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_COVER_OPEN_COMMAND): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                    vol.Required(CONF_COVER_CLOSE_COMMAND): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                    vol.Required(CONF_COVER_OPEN_FEEDBACK): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Required(CONF_COVER_CLOSED_FEEDBACK): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Required(CONF_COVER_OPENING_FEEDBACK): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Required(CONF_COVER_CLOSING_FEEDBACK): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Optional(CONF_COVER_CLOSED_PERCENT_FEEDBACK): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_COVER_BLADES_ENABLED, default=False): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_add_cover_blades(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Optionally complete one venetian blind with blade pulse controls."""
        if self._pending_cover is None:
            return self.async_abort(reason="cover_configuration_state_lost")

        errors: dict[str, str] = {}
        if user_input is not None:
            cover = dict(self._pending_cover)
            cover["commands"] = dict(cover["commands"])
            cover["commands"].update(
                {
                    "blades_open_entity_id": user_input[CONF_COVER_BLADES_OPEN_COMMAND],
                    "blades_close_entity_id": user_input[CONF_COVER_BLADES_CLOSE_COMMAND],
                }
            )
            cover["capabilities"] = ["open", "close", "blades_open", "blades_close"]
            try:
                result = await self.hass.async_add_executor_job(
                    _manager(self.hass).add_cover,
                    cover,
                )
            except WNHFConfigurationError as err:
                if "Semantic object ID already exists" in str(err):
                    errors["base"] = "cover_already_configured"
                else:
                    errors["base"] = "cannot_apply_object"
            else:
                self._pending_cover = None
                return self._finish(result.action)

        return self.async_show_form(
            step_id="add_cover_blades",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COVER_BLADES_OPEN_COMMAND): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                    vol.Required(CONF_COVER_BLADES_CLOSE_COMMAND): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_add_opening(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose which semantic opening type to add."""
        return self.async_show_menu(
            step_id="add_opening",
            menu_options=[
                "add_window",
                "add_sliding_door",
                "add_door",
                "add_garage_door",
            ],
        )

    async def _async_room_options(self) -> list[dict[str, str]] | None:
        """Return room selector options, or None if no room is configured."""
        try:
            room_options = await self.hass.async_add_executor_job(
                _manager(self.hass).room_options
            )
        except WNHFConfigurationError:
            return None
        return room_options or None

    async def _async_commit_opening(
        self,
        opening: dict[str, Any],
    ) -> tuple[FlowResult | None, str | None]:
        """Safely append one managed opening and normalize duplicate failures."""
        try:
            result = await self.hass.async_add_executor_job(
                _manager(self.hass).add_opening,
                opening,
            )
        except WNHFConfigurationError as err:
            if "Semantic object ID already exists" in str(err):
                return None, "opening_already_configured"
            return None, "cannot_apply_object"
        return self._finish(result.action), None

    async def _async_simple_opening_form(
        self,
        *,
        step_id: str,
        opening_type: str,
        user_input: dict[str, Any] | None,
    ) -> FlowResult:
        """Handle one simple window/sliding-door opening form."""
        room_options = await self._async_room_options()
        if room_options is None:
            return self.async_abort(reason="no_rooms_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_OPENING_NAME].strip()
            if not name:
                errors[CONF_OPENING_NAME] = "name_required"
            else:
                opening = _opening_state_entry(
                    room_id=user_input[CONF_ROOM_ID],
                    name=name,
                    opening_type=opening_type,
                    state_entity_id=user_input[CONF_OPENING_STATE_ENTITY_ID],
                )
                result, error = await self._async_commit_opening(opening)
                if result is not None:
                    return result
                if error == "opening_already_configured":
                    errors[CONF_OPENING_NAME] = error
                else:
                    errors["base"] = error or "cannot_apply_object"

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OPENING_NAME): str,
                    vol.Required(CONF_ROOM_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=room_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_OPENING_STATE_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_add_window(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add one window with objective binary open/closed feedback."""
        return await self._async_simple_opening_form(
            step_id="add_window",
            opening_type="window",
            user_input=user_input,
        )

    async def async_step_add_sliding_door(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add one sliding door with objective binary open/closed feedback."""
        return await self._async_simple_opening_form(
            step_id="add_sliding_door",
            opening_type="sliding_door",
            user_input=user_input,
        )

    async def async_step_add_door(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add one normal door, optionally followed by lock/opener modules."""
        room_options = await self._async_room_options()
        if room_options is None:
            return self.async_abort(reason="no_rooms_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_OPENING_NAME].strip()
            if not name:
                errors[CONF_OPENING_NAME] = "name_required"
            else:
                opening = _opening_state_entry(
                    room_id=user_input[CONF_ROOM_ID],
                    name=name,
                    opening_type="door",
                    state_entity_id=user_input[CONF_OPENING_STATE_ENTITY_ID],
                )
                configure_lock = user_input.get(CONF_DOOR_LOCK_ENABLED, False)
                configure_opener = user_input.get(CONF_DOOR_OPENER_ENABLED, False)
                if configure_lock or configure_opener:
                    self._pending_opening = opening
                    self._pending_door_opener_enabled = bool(configure_opener)
                    if configure_lock:
                        return await self.async_step_add_door_lock()
                    return await self.async_step_add_door_opener()

                result, error = await self._async_commit_opening(opening)
                if result is not None:
                    return result
                if error == "opening_already_configured":
                    errors[CONF_OPENING_NAME] = error
                else:
                    errors["base"] = error or "cannot_apply_object"

        return self.async_show_form(
            step_id="add_door",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OPENING_NAME): str,
                    vol.Required(CONF_ROOM_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=room_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_OPENING_STATE_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Required(CONF_DOOR_LOCK_ENABLED, default=False): bool,
                    vol.Required(CONF_DOOR_OPENER_ENABLED, default=False): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_add_door_lock(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Complete a normal door with objective motor-lock feedback and commands."""
        if self._pending_opening is None:
            return self.async_abort(reason="opening_configuration_state_lost")

        errors: dict[str, str] = {}
        if user_input is not None:
            opening = dict(self._pending_opening)
            opening["lock"] = {
                "enabled": True,
                "feedback": {
                    "entity_id": user_input[CONF_LOCK_FEEDBACK_ENTITY_ID],
                    "locked_states": ["on"],
                },
                "commands": {
                    "lock_entity_id": user_input[CONF_LOCK_COMMAND_ENTITY_ID],
                    "unlock_entity_id": user_input[CONF_UNLOCK_COMMAND_ENTITY_ID],
                },
            }
            self._pending_opening = opening
            if self._pending_door_opener_enabled:
                return await self.async_step_add_door_opener()

            result, error = await self._async_commit_opening(opening)
            if result is not None:
                self._pending_opening = None
                self._pending_door_opener_enabled = False
                return result
            errors["base"] = error or "cannot_apply_object"

        return self.async_show_form(
            step_id="add_door_lock",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOCK_FEEDBACK_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Required(CONF_LOCK_COMMAND_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                    vol.Required(CONF_UNLOCK_COMMAND_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_add_door_opener(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Complete a normal door with an electric door-release pulse."""
        if self._pending_opening is None:
            return self.async_abort(reason="opening_configuration_state_lost")

        errors: dict[str, str] = {}
        if user_input is not None:
            opening = dict(self._pending_opening)
            opening["door_opener"] = {
                "enabled": True,
                "command": {
                    "entity_id": user_input[CONF_DOOR_OPENER_COMMAND_ENTITY_ID],
                },
            }
            result, error = await self._async_commit_opening(opening)
            if result is not None:
                self._pending_opening = None
                self._pending_door_opener_enabled = False
                return result
            errors["base"] = error or "cannot_apply_object"

        return self.async_show_form(
            step_id="add_door_opener",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DOOR_OPENER_COMMAND_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_add_garage_door(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add one guarded garage door with dedicated two-sensor feedback."""
        room_options = await self._async_room_options()
        if room_options is None:
            return self.async_abort(reason="no_rooms_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_OPENING_NAME].strip()
            if not name:
                errors[CONF_OPENING_NAME] = "name_required"
            else:
                command = {
                    "toggle_entity_id": user_input[CONF_GARAGE_TOGGLE_COMMAND_ENTITY_ID],
                }
                stop_entity_id = user_input.get(CONF_GARAGE_STOP_COMMAND_ENTITY_ID)
                if stop_entity_id:
                    command["stop_entity_id"] = stop_entity_id
                opening = {
                    "id": _semantic_opening_id(
                        room_id=user_input[CONF_ROOM_ID],
                        opening_name=name,
                    ),
                    "name": name,
                    "room": user_input[CONF_ROOM_ID],
                    "type": "garage_door",
                    "enabled": True,
                    "garage": {
                        "enabled": True,
                        "feedback": {
                            "open_entity_id": user_input[
                                CONF_GARAGE_OPEN_FEEDBACK_ENTITY_ID
                            ],
                            "closed_entity_id": user_input[
                                CONF_GARAGE_CLOSED_FEEDBACK_ENTITY_ID
                            ],
                        },
                        "command": command,
                        "movement_timeout_seconds": float(
                            user_input[CONF_GARAGE_MOVEMENT_TIMEOUT_SECONDS]
                        ),
                    },
                }
                result, error = await self._async_commit_opening(opening)
                if result is not None:
                    return result
                if error == "opening_already_configured":
                    errors[CONF_OPENING_NAME] = error
                else:
                    errors["base"] = error or "cannot_apply_object"

        return self.async_show_form(
            step_id="add_garage_door",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OPENING_NAME): str,
                    vol.Required(CONF_ROOM_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=room_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_GARAGE_OPEN_FEEDBACK_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Required(CONF_GARAGE_CLOSED_FEEDBACK_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Required(CONF_GARAGE_TOGGLE_COMMAND_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                    vol.Optional(CONF_GARAGE_STOP_COMMAND_ENTITY_ID): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                    vol.Required(
                        CONF_GARAGE_MOVEMENT_TIMEOUT_SECONDS,
                        default=25.0,
                    ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=300.0)),
                }
            ),
            errors=errors,
        )

    async def async_step_add_plant(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add one semantic Plant Care object with automatic ID generation."""
        room_options = await self._async_room_options()
        if room_options is None:
            return self.async_abort(reason="no_rooms_configured")

        room_names = {
            str(option["value"]): str(option["label"])
            for option in room_options
        }
        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_PLANT_NAME].strip()
            species = user_input[CONF_PLANT_SPECIES].strip()
            room_id = user_input[CONF_ROOM_ID]
            location = str(user_input.get(CONF_PLANT_LOCATION) or "").strip()
            moisture_sensor = user_input.get(CONF_PLANT_MOISTURE_SENSOR_ENTITY_ID)

            if not name:
                errors[CONF_PLANT_NAME] = "name_required"
            elif not species:
                errors[CONF_PLANT_SPECIES] = "species_required"
            else:
                plant = {
                    "id": _semantic_plant_id(
                        room_id=room_id,
                        plant_name=name,
                    ),
                    "name": name,
                    "species": species,
                    "room": room_id,
                    "location": location or room_names.get(room_id, room_id),
                    "watering_interval_days": int(
                        user_input[CONF_PLANT_WATERING_INTERVAL_DAYS]
                    ),
                    "enabled": True,
                }
                if moisture_sensor:
                    plant["moisture_sensor_entity_id"] = moisture_sensor

                try:
                    result = await self.hass.async_add_executor_job(
                        _manager(self.hass).add_plant,
                        plant,
                    )
                except WNHFConfigurationError as err:
                    if "Semantic object ID already exists" in str(err):
                        errors[CONF_PLANT_NAME] = "plant_already_configured"
                    else:
                        errors["base"] = "cannot_apply_object"
                else:
                    return self._finish(result.action)

        return self.async_show_form(
            step_id="add_plant",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PLANT_NAME): str,
                    vol.Required(CONF_PLANT_SPECIES): str,
                    vol.Required(CONF_ROOM_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=room_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(CONF_PLANT_LOCATION, default=""): str,
                    vol.Required(
                        CONF_PLANT_WATERING_INTERVAL_DAYS,
                        default=7,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=365)),
                    vol.Optional(
                        CONF_PLANT_MOISTURE_SENSOR_ENTITY_ID
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                }
            ),
            errors=errors,
        )


    async def async_step_manage(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Open the managed-object maintenance area."""
        return self.async_show_menu(
            step_id="manage",
            menu_options=[
                "manage_room",
                "manage_light",
                "manage_cover",
                "manage_opening",
                "manage_plant",
            ],
        )

    async def _async_select_managed_object(
        self,
        *,
        object_type: str,
        step_id: str,
        next_step: str,
        user_input: dict[str, Any] | None,
    ) -> FlowResult:
        """Select one configurator-owned object and enter its edit form."""
        manager = _manager(self.hass)
        try:
            options = await self.hass.async_add_executor_job(
                manager.object_options,
                object_type,
            )
        except WNHFConfigurationError:
            return self.async_abort(reason="maintenance_unavailable")
        if not options:
            return self.async_abort(reason="no_managed_objects")

        errors: dict[str, str] = {}
        if user_input is not None:
            object_id = user_input[CONF_OBJECT_ID]
            try:
                current = await self.hass.async_add_executor_job(
                    manager.get_object,
                    object_type,
                    object_id,
                )
            except WNHFConfigurationError:
                errors[CONF_OBJECT_ID] = "object_not_found"
            else:
                self._pending_object_type = object_type
                self._pending_object = current
                return await getattr(self, f"async_step_{next_step}")()

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OBJECT_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def async_step_manage_room(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self._async_select_managed_object(
            object_type="rooms",
            step_id="manage_room",
            next_step="edit_room",
            user_input=user_input,
        )

    async def async_step_manage_light(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self._async_select_managed_object(
            object_type="lights",
            step_id="manage_light",
            next_step="edit_light",
            user_input=user_input,
        )

    async def async_step_manage_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self._async_select_managed_object(
            object_type="covers",
            step_id="manage_cover",
            next_step="edit_cover",
            user_input=user_input,
        )

    async def async_step_manage_plant(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self._async_select_managed_object(
            object_type="plants",
            step_id="manage_plant",
            next_step="edit_plant",
            user_input=user_input,
        )

    async def async_step_manage_opening(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select one opening and route to its type-specific maintenance form."""
        manager = _manager(self.hass)
        try:
            options = await self.hass.async_add_executor_job(
                manager.object_options,
                "openings",
            )
        except WNHFConfigurationError:
            return self.async_abort(reason="maintenance_unavailable")
        if not options:
            return self.async_abort(reason="no_managed_objects")

        errors: dict[str, str] = {}
        if user_input is not None:
            object_id = user_input[CONF_OBJECT_ID]
            try:
                current = await self.hass.async_add_executor_job(
                    manager.get_object,
                    "openings",
                    object_id,
                )
            except WNHFConfigurationError:
                errors[CONF_OBJECT_ID] = "object_not_found"
            else:
                self._pending_object_type = "openings"
                self._pending_object = current
                next_steps = {
                    "window": "edit_window",
                    "sliding_door": "edit_sliding_door",
                    "door": "edit_door",
                    "garage_door": "edit_garage_door",
                }
                next_step = next_steps.get(str(current.get("type")))
                if next_step is None:
                    errors[CONF_OBJECT_ID] = "unsupported_opening_type"
                else:
                    return await getattr(self, f"async_step_{next_step}")()

        return self.async_show_form(
            step_id="manage_opening",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OBJECT_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=errors,
        )

    def _maintenance_current(self, object_type: str) -> dict[str, Any] | None:
        """Return the selected object only while the expected edit flow owns it."""
        if self._pending_object_type != object_type or self._pending_object is None:
            return None
        return self._pending_object

    async def _async_commit_pending_update(
        self,
        replacement: dict[str, Any],
    ) -> tuple[FlowResult | None, str | None]:
        """Transactionally update the selected managed object."""
        current = self._pending_object
        object_type = self._pending_object_type
        if current is None or object_type is None:
            return None, "maintenance_state_lost"
        try:
            result = await self.hass.async_add_executor_job(
                _manager(self.hass).update_object,
                object_type,
                str(current["id"]),
                replacement,
            )
        except WNHFConfigurationError:
            return None, "cannot_apply_object"

        self._pending_object = None
        self._pending_object_type = None
        return self._finish(result.action), None

    async def async_step_edit_room(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Maintain a room without changing its stable semantic ID/source link."""
        current = self._maintenance_current("rooms")
        if current is None:
            return self.async_abort(reason="maintenance_state_lost")

        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_DELETE_OBJECT, False):
                return await self.async_step_delete_confirm()
            name = str(user_input["name"]).strip()
            if not name:
                errors["name"] = "name_required"
            else:
                replacement = deepcopy(current)
                replacement["name"] = name
                replacement["enabled"] = bool(user_input[CONF_ENABLED])
                result, error = await self._async_commit_pending_update(replacement)
                if result is not None:
                    return result
                errors["base"] = error or "cannot_apply_object"

        defaults = user_input or {}
        return self.async_show_form(
            step_id="edit_room",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "name",
                        default=defaults.get("name", current.get("name", "")),
                    ): str,
                    vol.Required(
                        CONF_ENABLED,
                        default=defaults.get(
                            CONF_ENABLED, bool(current.get("enabled", True))
                        ),
                    ): bool,
                    vol.Required(
                        CONF_DELETE_OBJECT,
                        default=defaults.get(CONF_DELETE_OBJECT, False),
                    ): bool,
                }
            ),
            errors=errors,
            description_placeholders={"object_id": str(current["id"])},
        )

    async def async_step_edit_light(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Maintain one impulse light while preserving its semantic ID."""
        current = self._maintenance_current("lights")
        if current is None:
            return self.async_abort(reason="maintenance_state_lost")
        room_options = await self._async_room_options()
        if room_options is None:
            return self.async_abort(reason="no_rooms_configured")

        command = current.get("command") or {}
        state = current.get("state") or {}
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_DELETE_OBJECT, False):
                return await self.async_step_delete_confirm()
            name = str(user_input["name"]).strip()
            if not name:
                errors["name"] = "name_required"
            else:
                replacement = deepcopy(current)
                replacement["name"] = name
                replacement["room"] = user_input[CONF_ROOM_ID]
                replacement["enabled"] = bool(user_input[CONF_ENABLED])
                replacement["command"] = {
                    **dict(command),
                    "entity_id": user_input[CONF_COMMAND_ENTITY_ID],
                }
                replacement["state"] = {
                    **dict(state),
                    "entity_id": user_input[CONF_FEEDBACK_ENTITY_ID],
                }
                result, error = await self._async_commit_pending_update(replacement)
                if result is not None:
                    return result
                errors["base"] = error or "cannot_apply_object"

        defaults = user_input or {}
        return self.async_show_form(
            step_id="edit_light",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "name",
                        default=defaults.get("name", current.get("name", "")),
                    ): str,
                    vol.Required(
                        CONF_ROOM_ID,
                        default=defaults.get(CONF_ROOM_ID, current.get("room")),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=room_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(
                        CONF_COMMAND_ENTITY_ID,
                        default=defaults.get(
                            CONF_COMMAND_ENTITY_ID, command.get("entity_id")
                        ),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="button")
                    ),
                    vol.Required(
                        CONF_FEEDBACK_ENTITY_ID,
                        default=defaults.get(
                            CONF_FEEDBACK_ENTITY_ID, state.get("entity_id")
                        ),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Required(
                        CONF_ENABLED,
                        default=defaults.get(
                            CONF_ENABLED, bool(current.get("enabled", True))
                        ),
                    ): bool,
                    vol.Required(
                        CONF_DELETE_OBJECT,
                        default=defaults.get(CONF_DELETE_OBJECT, False),
                    ): bool,
                }
            ),
            errors=errors,
            description_placeholders={"object_id": str(current["id"])},
        )

    async def async_step_edit_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Maintain one venetian blind and its optional blade pulse controls."""
        current = self._maintenance_current("covers")
        if current is None:
            return self.async_abort(reason="maintenance_state_lost")
        room_options = await self._async_room_options()
        if room_options is None:
            return self.async_abort(reason="no_rooms_configured")

        commands = dict(current.get("commands") or {})
        feedback = dict(current.get("feedback") or {})
        capabilities = list(current.get("capabilities") or [])
        has_blades = (
            "blades_open" in capabilities
            or bool(commands.get("blades_open_entity_id"))
            or bool(commands.get("blades_close_entity_id"))
        )
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get(CONF_DELETE_OBJECT, False):
                return await self.async_step_delete_confirm()
            name = str(user_input[CONF_COVER_NAME]).strip()
            blades_enabled = bool(user_input.get(CONF_COVER_BLADES_ENABLED, False))
            if not name:
                errors[CONF_COVER_NAME] = "name_required"
            elif blades_enabled and not user_input.get(CONF_COVER_BLADES_OPEN_COMMAND):
                errors[CONF_COVER_BLADES_OPEN_COMMAND] = "entity_required"
            elif blades_enabled and not user_input.get(CONF_COVER_BLADES_CLOSE_COMMAND):
                errors[CONF_COVER_BLADES_CLOSE_COMMAND] = "entity_required"
            else:
                replacement = deepcopy(current)
                replacement["name"] = name
                replacement["room"] = user_input[CONF_ROOM_ID]
                replacement["enabled"] = bool(user_input[CONF_ENABLED])
                next_commands = dict(commands)
                next_commands["open_entity_id"] = user_input[CONF_COVER_OPEN_COMMAND]
                next_commands["close_entity_id"] = user_input[CONF_COVER_CLOSE_COMMAND]
                if blades_enabled:
                    next_commands["blades_open_entity_id"] = user_input[
                        CONF_COVER_BLADES_OPEN_COMMAND
                    ]
                    next_commands["blades_close_entity_id"] = user_input[
                        CONF_COVER_BLADES_CLOSE_COMMAND
                    ]
                    replacement["capabilities"] = [
                        "open",
                        "close",
                        "blades_open",
                        "blades_close",
                    ]
                else:
                    next_commands.pop("blades_open_entity_id", None)
                    next_commands.pop("blades_close_entity_id", None)
                    replacement["capabilities"] = ["open", "close"]
                replacement["commands"] = next_commands

                next_feedback = dict(feedback)
                next_feedback.update(
                    {
                        "open_entity_id": user_input[CONF_COVER_OPEN_FEEDBACK],
                        "closed_entity_id": user_input[CONF_COVER_CLOSED_FEEDBACK],
                        "opening_entity_id": user_input[CONF_COVER_OPENING_FEEDBACK],
                        "closing_entity_id": user_input[CONF_COVER_CLOSING_FEEDBACK],
                    }
                )
                closed_percent = user_input.get(CONF_COVER_CLOSED_PERCENT_FEEDBACK)
                if closed_percent:
                    next_feedback["closed_percent_entity_id"] = closed_percent
                else:
                    next_feedback.pop("closed_percent_entity_id", None)
                replacement["feedback"] = next_feedback

                result, error = await self._async_commit_pending_update(replacement)
                if result is not None:
                    return result
                errors["base"] = error or "cannot_apply_object"

        defaults = user_input or {}
        schema: dict[Any, Any] = {
            vol.Required(
                CONF_COVER_NAME,
                default=defaults.get(CONF_COVER_NAME, current.get("name", "")),
            ): str,
            vol.Required(
                CONF_ROOM_ID,
                default=defaults.get(CONF_ROOM_ID, current.get("room")),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=room_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_COVER_OPEN_COMMAND,
                default=defaults.get(
                    CONF_COVER_OPEN_COMMAND, commands.get("open_entity_id")
                ),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="button")),
            vol.Required(
                CONF_COVER_CLOSE_COMMAND,
                default=defaults.get(
                    CONF_COVER_CLOSE_COMMAND, commands.get("close_entity_id")
                ),
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain="button")),
            vol.Required(
                CONF_COVER_OPEN_FEEDBACK,
                default=defaults.get(
                    CONF_COVER_OPEN_FEEDBACK, feedback.get("open_entity_id")
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Required(
                CONF_COVER_CLOSED_FEEDBACK,
                default=defaults.get(
                    CONF_COVER_CLOSED_FEEDBACK, feedback.get("closed_entity_id")
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Required(
                CONF_COVER_OPENING_FEEDBACK,
                default=defaults.get(
                    CONF_COVER_OPENING_FEEDBACK, feedback.get("opening_entity_id")
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Required(
                CONF_COVER_CLOSING_FEEDBACK,
                default=defaults.get(
                    CONF_COVER_CLOSING_FEEDBACK, feedback.get("closing_entity_id")
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Required(
                CONF_COVER_BLADES_ENABLED,
                default=defaults.get(CONF_COVER_BLADES_ENABLED, has_blades),
            ): bool,
            vol.Required(
                CONF_ENABLED,
                default=defaults.get(CONF_ENABLED, bool(current.get("enabled", True))),
            ): bool,
            vol.Required(
                CONF_DELETE_OBJECT,
                default=defaults.get(CONF_DELETE_OBJECT, False),
            ): bool,
        }

        closed_percent_default = defaults.get(
            CONF_COVER_CLOSED_PERCENT_FEEDBACK,
            feedback.get("closed_percent_entity_id"),
        )
        closed_percent_marker = (
            vol.Optional(
                CONF_COVER_CLOSED_PERCENT_FEEDBACK,
                default=closed_percent_default,
            )
            if closed_percent_default
            else vol.Optional(CONF_COVER_CLOSED_PERCENT_FEEDBACK)
        )
        schema[closed_percent_marker] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        )

        blade_open_default = defaults.get(
            CONF_COVER_BLADES_OPEN_COMMAND,
            commands.get("blades_open_entity_id"),
        )
        blade_open_marker = (
            vol.Optional(CONF_COVER_BLADES_OPEN_COMMAND, default=blade_open_default)
            if blade_open_default
            else vol.Optional(CONF_COVER_BLADES_OPEN_COMMAND)
        )
        schema[blade_open_marker] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="button")
        )

        blade_close_default = defaults.get(
            CONF_COVER_BLADES_CLOSE_COMMAND,
            commands.get("blades_close_entity_id"),
        )
        blade_close_marker = (
            vol.Optional(CONF_COVER_BLADES_CLOSE_COMMAND, default=blade_close_default)
            if blade_close_default
            else vol.Optional(CONF_COVER_BLADES_CLOSE_COMMAND)
        )
        schema[blade_close_marker] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="button")
        )

        return self.async_show_form(
            step_id="edit_cover",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={"object_id": str(current["id"])},
        )

    async def _async_edit_simple_opening(
        self,
        *,
        step_id: str,
        user_input: dict[str, Any] | None,
    ) -> FlowResult:
        """Maintain a window or sliding door."""
        current = self._maintenance_current("openings")
        if current is None:
            return self.async_abort(reason="maintenance_state_lost")
        room_options = await self._async_room_options()
        if room_options is None:
            return self.async_abort(reason="no_rooms_configured")

        state = dict(current.get("state") or {})
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_DELETE_OBJECT, False):
                return await self.async_step_delete_confirm()
            name = str(user_input[CONF_OPENING_NAME]).strip()
            if not name:
                errors[CONF_OPENING_NAME] = "name_required"
            else:
                replacement = deepcopy(current)
                replacement["name"] = name
                replacement["room"] = user_input[CONF_ROOM_ID]
                replacement["enabled"] = bool(user_input[CONF_ENABLED])
                replacement["state"] = {
                    **state,
                    "entity_id": user_input[CONF_OPENING_STATE_ENTITY_ID],
                }
                result, error = await self._async_commit_pending_update(replacement)
                if result is not None:
                    return result
                errors["base"] = error or "cannot_apply_object"

        defaults = user_input or {}
        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_OPENING_NAME,
                        default=defaults.get(
                            CONF_OPENING_NAME, current.get("name", "")
                        ),
                    ): str,
                    vol.Required(
                        CONF_ROOM_ID,
                        default=defaults.get(CONF_ROOM_ID, current.get("room")),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=room_options,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(
                        CONF_OPENING_STATE_ENTITY_ID,
                        default=defaults.get(
                            CONF_OPENING_STATE_ENTITY_ID, state.get("entity_id")
                        ),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="binary_sensor")
                    ),
                    vol.Required(
                        CONF_ENABLED,
                        default=defaults.get(
                            CONF_ENABLED, bool(current.get("enabled", True))
                        ),
                    ): bool,
                    vol.Required(
                        CONF_DELETE_OBJECT,
                        default=defaults.get(CONF_DELETE_OBJECT, False),
                    ): bool,
                }
            ),
            errors=errors,
            description_placeholders={"object_id": str(current["id"])},
        )

    async def async_step_edit_window(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self._async_edit_simple_opening(
            step_id="edit_window", user_input=user_input
        )

    async def async_step_edit_sliding_door(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self._async_edit_simple_opening(
            step_id="edit_sliding_door", user_input=user_input
        )

    async def async_step_edit_door(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Maintain a normal door including optional lock and opener modules."""
        current = self._maintenance_current("openings")
        if current is None:
            return self.async_abort(reason="maintenance_state_lost")
        room_options = await self._async_room_options()
        if room_options is None:
            return self.async_abort(reason="no_rooms_configured")

        state = dict(current.get("state") or {})
        lock = dict(current.get("lock") or {})
        lock_feedback = dict(lock.get("feedback") or {})
        lock_commands = dict(lock.get("commands") or {})
        opener = dict(current.get("door_opener") or {})
        opener_command = dict(opener.get("command") or {})

        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_DELETE_OBJECT, False):
                return await self.async_step_delete_confirm()
            name = str(user_input[CONF_OPENING_NAME]).strip()
            configure_lock = bool(user_input.get(CONF_DOOR_LOCK_ENABLED, False))
            configure_opener = bool(user_input.get(CONF_DOOR_OPENER_ENABLED, False))
            if not name:
                errors[CONF_OPENING_NAME] = "name_required"
            elif configure_lock and not user_input.get(CONF_LOCK_FEEDBACK_ENTITY_ID):
                errors[CONF_LOCK_FEEDBACK_ENTITY_ID] = "entity_required"
            elif configure_lock and not user_input.get(CONF_LOCK_COMMAND_ENTITY_ID):
                errors[CONF_LOCK_COMMAND_ENTITY_ID] = "entity_required"
            elif configure_lock and not user_input.get(CONF_UNLOCK_COMMAND_ENTITY_ID):
                errors[CONF_UNLOCK_COMMAND_ENTITY_ID] = "entity_required"
            elif configure_opener and not user_input.get(
                CONF_DOOR_OPENER_COMMAND_ENTITY_ID
            ):
                errors[CONF_DOOR_OPENER_COMMAND_ENTITY_ID] = "entity_required"
            else:
                replacement = deepcopy(current)
                replacement["name"] = name
                replacement["room"] = user_input[CONF_ROOM_ID]
                replacement["enabled"] = bool(user_input[CONF_ENABLED])
                replacement["state"] = {
                    **state,
                    "entity_id": user_input[CONF_OPENING_STATE_ENTITY_ID],
                }

                if configure_lock:
                    replacement["lock"] = {
                        **lock,
                        "enabled": True,
                        "feedback": {
                            **lock_feedback,
                            "entity_id": user_input[CONF_LOCK_FEEDBACK_ENTITY_ID],
                            "locked_states": lock_feedback.get(
                                "locked_states", ["on"]
                            ),
                        },
                        "commands": {
                            **lock_commands,
                            "lock_entity_id": user_input[CONF_LOCK_COMMAND_ENTITY_ID],
                            "unlock_entity_id": user_input[
                                CONF_UNLOCK_COMMAND_ENTITY_ID
                            ],
                        },
                    }
                else:
                    replacement.pop("lock", None)

                if configure_opener:
                    replacement["door_opener"] = {
                        **opener,
                        "enabled": True,
                        "command": {
                            **opener_command,
                            "entity_id": user_input[
                                CONF_DOOR_OPENER_COMMAND_ENTITY_ID
                            ],
                        },
                    }
                else:
                    replacement.pop("door_opener", None)

                result, error = await self._async_commit_pending_update(replacement)
                if result is not None:
                    return result
                errors["base"] = error or "cannot_apply_object"

        defaults = user_input or {}
        schema: dict[Any, Any] = {
            vol.Required(
                CONF_OPENING_NAME,
                default=defaults.get(CONF_OPENING_NAME, current.get("name", "")),
            ): str,
            vol.Required(
                CONF_ROOM_ID,
                default=defaults.get(CONF_ROOM_ID, current.get("room")),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=room_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_OPENING_STATE_ENTITY_ID,
                default=defaults.get(
                    CONF_OPENING_STATE_ENTITY_ID, state.get("entity_id")
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Required(
                CONF_DOOR_LOCK_ENABLED,
                default=defaults.get(
                    CONF_DOOR_LOCK_ENABLED, bool(lock.get("enabled", False))
                ),
            ): bool,
            vol.Required(
                CONF_DOOR_OPENER_ENABLED,
                default=defaults.get(
                    CONF_DOOR_OPENER_ENABLED, bool(opener.get("enabled", False))
                ),
            ): bool,
            vol.Required(
                CONF_ENABLED,
                default=defaults.get(CONF_ENABLED, bool(current.get("enabled", True))),
            ): bool,
            vol.Required(
                CONF_DELETE_OBJECT,
                default=defaults.get(CONF_DELETE_OBJECT, False),
            ): bool,
        }

        optional_entities = (
            (
                CONF_LOCK_FEEDBACK_ENTITY_ID,
                "binary_sensor",
                lock_feedback.get("entity_id"),
            ),
            (
                CONF_LOCK_COMMAND_ENTITY_ID,
                "button",
                lock_commands.get("lock_entity_id"),
            ),
            (
                CONF_UNLOCK_COMMAND_ENTITY_ID,
                "button",
                lock_commands.get("unlock_entity_id"),
            ),
            (
                CONF_DOOR_OPENER_COMMAND_ENTITY_ID,
                "button",
                opener_command.get("entity_id"),
            ),
        )
        for key, domain, current_default in optional_entities:
            default_value = defaults.get(key, current_default)
            marker = (
                vol.Optional(key, default=default_value)
                if default_value
                else vol.Optional(key)
            )
            schema[marker] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain=domain)
            )

        return self.async_show_form(
            step_id="edit_door",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={"object_id": str(current["id"])},
        )

    async def async_step_edit_garage_door(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Maintain one guarded garage door without weakening execution guards."""
        current = self._maintenance_current("openings")
        if current is None:
            return self.async_abort(reason="maintenance_state_lost")
        room_options = await self._async_room_options()
        if room_options is None:
            return self.async_abort(reason="no_rooms_configured")

        garage = dict(current.get("garage") or {})
        feedback = dict(garage.get("feedback") or {})
        command = dict(garage.get("command") or {})
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get(CONF_DELETE_OBJECT, False):
                return await self.async_step_delete_confirm()
            name = str(user_input[CONF_OPENING_NAME]).strip()
            if not name:
                errors[CONF_OPENING_NAME] = "name_required"
            else:
                enabled = bool(user_input[CONF_ENABLED])
                replacement = deepcopy(current)
                replacement["name"] = name
                replacement["room"] = user_input[CONF_ROOM_ID]
                replacement["enabled"] = enabled
                next_command = {
                    **command,
                    "toggle_entity_id": user_input[
                        CONF_GARAGE_TOGGLE_COMMAND_ENTITY_ID
                    ],
                }
                stop_entity = user_input.get(CONF_GARAGE_STOP_COMMAND_ENTITY_ID)
                if stop_entity:
                    next_command["stop_entity_id"] = stop_entity
                else:
                    next_command.pop("stop_entity_id", None)

                replacement["garage"] = {
                    **garage,
                    "enabled": enabled,
                    "feedback": {
                        **feedback,
                        "open_entity_id": user_input[
                            CONF_GARAGE_OPEN_FEEDBACK_ENTITY_ID
                        ],
                        "closed_entity_id": user_input[
                            CONF_GARAGE_CLOSED_FEEDBACK_ENTITY_ID
                        ],
                    },
                    "command": next_command,
                    "movement_timeout_seconds": float(
                        user_input[CONF_GARAGE_MOVEMENT_TIMEOUT_SECONDS]
                    ),
                }
                result, error = await self._async_commit_pending_update(replacement)
                if result is not None:
                    return result
                errors["base"] = error or "cannot_apply_object"

        defaults = user_input or {}
        schema: dict[Any, Any] = {
            vol.Required(
                CONF_OPENING_NAME,
                default=defaults.get(CONF_OPENING_NAME, current.get("name", "")),
            ): str,
            vol.Required(
                CONF_ROOM_ID,
                default=defaults.get(CONF_ROOM_ID, current.get("room")),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=room_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_GARAGE_OPEN_FEEDBACK_ENTITY_ID,
                default=defaults.get(
                    CONF_GARAGE_OPEN_FEEDBACK_ENTITY_ID,
                    feedback.get("open_entity_id"),
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Required(
                CONF_GARAGE_CLOSED_FEEDBACK_ENTITY_ID,
                default=defaults.get(
                    CONF_GARAGE_CLOSED_FEEDBACK_ENTITY_ID,
                    feedback.get("closed_entity_id"),
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            vol.Required(
                CONF_GARAGE_TOGGLE_COMMAND_ENTITY_ID,
                default=defaults.get(
                    CONF_GARAGE_TOGGLE_COMMAND_ENTITY_ID,
                    command.get("toggle_entity_id"),
                ),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="button")
            ),
            vol.Required(
                CONF_GARAGE_MOVEMENT_TIMEOUT_SECONDS,
                default=defaults.get(
                    CONF_GARAGE_MOVEMENT_TIMEOUT_SECONDS,
                    float(garage.get("movement_timeout_seconds", 25.0)),
                ),
            ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=300.0)),
            vol.Required(
                CONF_ENABLED,
                default=defaults.get(CONF_ENABLED, bool(current.get("enabled", True))),
            ): bool,
            vol.Required(
                CONF_DELETE_OBJECT,
                default=defaults.get(CONF_DELETE_OBJECT, False),
            ): bool,
        }
        stop_default = defaults.get(
            CONF_GARAGE_STOP_COMMAND_ENTITY_ID, command.get("stop_entity_id")
        )
        stop_marker = (
            vol.Optional(CONF_GARAGE_STOP_COMMAND_ENTITY_ID, default=stop_default)
            if stop_default
            else vol.Optional(CONF_GARAGE_STOP_COMMAND_ENTITY_ID)
        )
        schema[stop_marker] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="button")
        )

        return self.async_show_form(
            step_id="edit_garage_door",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={"object_id": str(current["id"])},
        )

    async def async_step_edit_plant(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Maintain Plant Care metadata while keeping watering-history identity."""
        current = self._maintenance_current("plants")
        if current is None:
            return self.async_abort(reason="maintenance_state_lost")
        room_options = await self._async_room_options()
        if room_options is None:
            return self.async_abort(reason="no_rooms_configured")

        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get(CONF_DELETE_OBJECT, False):
                return await self.async_step_delete_confirm()
            name = str(user_input[CONF_PLANT_NAME]).strip()
            species = str(user_input[CONF_PLANT_SPECIES]).strip()
            if not name:
                errors[CONF_PLANT_NAME] = "name_required"
            elif not species:
                errors[CONF_PLANT_SPECIES] = "species_required"
            else:
                replacement = deepcopy(current)
                replacement["name"] = name
                replacement["species"] = species
                replacement["room"] = user_input[CONF_ROOM_ID]
                replacement["location"] = str(
                    user_input.get(CONF_PLANT_LOCATION) or ""
                ).strip()
                replacement["watering_interval_days"] = int(
                    user_input[CONF_PLANT_WATERING_INTERVAL_DAYS]
                )
                replacement["enabled"] = bool(user_input[CONF_ENABLED])
                moisture = user_input.get(CONF_PLANT_MOISTURE_SENSOR_ENTITY_ID)
                if moisture:
                    replacement["moisture_sensor_entity_id"] = moisture
                else:
                    replacement.pop("moisture_sensor_entity_id", None)

                result, error = await self._async_commit_pending_update(replacement)
                if result is not None:
                    return result
                errors["base"] = error or "cannot_apply_object"

        defaults = user_input or {}
        schema: dict[Any, Any] = {
            vol.Required(
                CONF_PLANT_NAME,
                default=defaults.get(CONF_PLANT_NAME, current.get("name", "")),
            ): str,
            vol.Required(
                CONF_PLANT_SPECIES,
                default=defaults.get(
                    CONF_PLANT_SPECIES, current.get("species", "")
                ),
            ): str,
            vol.Required(
                CONF_ROOM_ID,
                default=defaults.get(CONF_ROOM_ID, current.get("room")),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=room_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_PLANT_LOCATION,
                default=defaults.get(
                    CONF_PLANT_LOCATION, current.get("location", "")
                ),
            ): str,
            vol.Required(
                CONF_PLANT_WATERING_INTERVAL_DAYS,
                default=defaults.get(
                    CONF_PLANT_WATERING_INTERVAL_DAYS,
                    int(current.get("watering_interval_days", 7)),
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=365)),
            vol.Required(
                CONF_ENABLED,
                default=defaults.get(CONF_ENABLED, bool(current.get("enabled", True))),
            ): bool,
            vol.Required(
                CONF_DELETE_OBJECT,
                default=defaults.get(CONF_DELETE_OBJECT, False),
            ): bool,
        }
        moisture_default = defaults.get(
            CONF_PLANT_MOISTURE_SENSOR_ENTITY_ID,
            current.get("moisture_sensor_entity_id"),
        )
        moisture_marker = (
            vol.Optional(
                CONF_PLANT_MOISTURE_SENSOR_ENTITY_ID,
                default=moisture_default,
            )
            if moisture_default
            else vol.Optional(CONF_PLANT_MOISTURE_SENSOR_ENTITY_ID)
        )
        schema[moisture_marker] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        )

        return self.async_show_form(
            step_id="edit_plant",
            data_schema=vol.Schema(schema),
            errors=errors,
            description_placeholders={"object_id": str(current["id"])},
        )

    async def async_step_delete_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Require an explicit second confirmation before deleting an object."""
        current = self._pending_object
        object_type = self._pending_object_type
        if current is None or object_type is None:
            return self.async_abort(reason="maintenance_state_lost")

        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_CONFIRM, False):
                errors["base"] = "confirmation_required"
            else:
                try:
                    result = await self.hass.async_add_executor_job(
                        _manager(self.hass).delete_object,
                        object_type,
                        str(current["id"]),
                    )
                except WNHFConfigurationError as err:
                    message = str(err)
                    if (
                        "Room is still referenced" in message
                        or "At least one managed room" in message
                    ):
                        errors["base"] = "object_in_use"
                    else:
                        errors["base"] = "cannot_delete_object"
                else:
                    self._pending_object = None
                    self._pending_object_type = None
                    return self._finish(result.action)

        return self.async_show_form(
            step_id="delete_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_CONFIRM, default=False): bool}
            ),
            errors=errors,
            description_placeholders={
                "object_type": object_type,
                "object_name": str(current.get("name") or current["id"]),
                "object_id": str(current["id"]),
            },
        )

    async def async_step_dashboard(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show dashboard status and exactly one explicit write action."""
        try:
            status = await dashboard_generation_service(self.hass).async_status()
        except DashboardGenerationError as err:
            return self.async_abort(
                reason="dashboard_generation_failed",
                description_placeholders={"error": str(err)},
            )

        action = (
            "dashboard_create"
            if status.lifecycle.state == "not_created"
            else "dashboard_update"
        )
        return self.async_show_menu(
            step_id="dashboard",
            menu_options=[action],
            description_placeholders=_dashboard_placeholders(self.hass, status),
        )

    async def async_step_dashboard_create(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Explicitly create the integration-owned Red Queen dashboard."""
        return await self._async_apply_dashboard()

    async def async_step_dashboard_update(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Explicitly refresh the integration-owned Red Queen dashboard."""
        return await self._async_apply_dashboard()

    async def _async_apply_dashboard(self) -> FlowResult:
        """Run the dashboard generation pipeline after an explicit click."""
        try:
            result = await dashboard_generation_service(self.hass).async_apply()
        except DashboardGenerationError as err:
            return self.async_abort(
                reason="dashboard_generation_failed",
                description_placeholders={"error": str(err)},
            )

        return self._finish_dashboard(
            action=result.applied.action,
            dashboard_path=f"/{result.applied.status.url_path}",
        )

    def _finish_dashboard(
        self,
        *,
        action: str,
        dashboard_path: str,
    ) -> FlowResult:
        """Finish a dashboard action without reloading the integration mid-flow."""
        configuration_action = f"dashboard_{action}"
        options = dict(self.config_entry.options)
        options.update(
            {
                "last_configuration_action": configuration_action,
                "last_configuration_at": datetime.now(UTC).isoformat(),
                "dashboard_refresh_recommended": False,
            }
        )

        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options=options,
        )

        reason = (
            "dashboard_created"
            if action == "create"
            else "dashboard_updated"
        )
        return self.async_abort(
            reason=reason,
            description_placeholders={"dashboard_path": dashboard_path},
        )

    def _finish_repair(self, result) -> FlowResult:
        """Finish one accepted repair and retain its transaction backup path."""
        options = dict(self.config_entry.options)
        options.update(
            {
                "last_configuration_action": result.action,
                "last_configuration_at": datetime.now(UTC).isoformat(),
                "last_configuration_backup_path": result.backup_path,
                "dashboard_refresh_recommended": True,
            }
        )
        return self.async_create_entry(title="", data=options)

    def _finish_migration(
        self,
        *,
        result,
        source_sha256: str,
    ) -> FlowResult:
        data = dict(self.config_entry.data)
        data["registry_mode"] = CONFIGURATOR_MODE_MANAGED
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=data,
        )

        options = dict(self.config_entry.options)
        options.update(
            {
                "last_configuration_action": result.action,
                "last_configuration_at": datetime.now(UTC).isoformat(),
                "last_configuration_backup_path": result.backup_path,
                "last_migration_source_sha256": source_sha256,
                "dashboard_refresh_recommended": True,
            }
        )
        return self.async_create_entry(title="", data=options)

    def _finish(self, action: str) -> FlowResult:
        options = dict(self.config_entry.options)
        options.update(
            {
                "last_configuration_action": action,
                "last_configuration_at": datetime.now(UTC).isoformat(),
            }
        )
        options["dashboard_refresh_recommended"] = not action.startswith(
            "dashboard_"
        )
        return self.async_create_entry(title="", data=options)
