"""Config and options flows for safe Red Queen commissioning."""

from __future__ import annotations

from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import area_registry as ar, floor_registry as fr, selector
from homeassistant.util import slugify

from .configuration import (
    CONFIGURATOR_MODE_MANAGED,
    CONFIGURATOR_MODE_MANUAL,
    RegistryConfigurationManager,
    WNHFConfigurationError,
)
from .const import DOMAIN, PRODUCT_NAME, REGISTRY_ROOT

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
    """Inspect or safely extend configurator-managed registries."""

    def __init__(self) -> None:
        self._pending_base: dict[str, Any] | None = None
        self._pending_cover: dict[str, Any] | None = None
        self._pending_opening: dict[str, Any] | None = None
        self._pending_door_opener_enabled = False

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        snapshot = await self.hass.async_add_executor_job(_manager(self.hass).snapshot)
        if snapshot["mode"] == "uninitialized":
            return await self.async_step_create_base()
        if snapshot["mode"] == CONFIGURATOR_MODE_MANUAL:
            return await self.async_step_status()
        return self.async_show_menu(
            step_id="init",
            menu_options=["status", "add_room", "add_light", "add_cover", "add_opening", "add_plant"],
            description_placeholders=_status_placeholders(snapshot),
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

    def _finish(self, action: str) -> FlowResult:
        options = dict(self.config_entry.options)
        options.update(
            {
                "last_configuration_action": action,
                "last_configuration_at": datetime.now(UTC).isoformat(),
            }
        )
        return self.async_create_entry(title="", data=options)
