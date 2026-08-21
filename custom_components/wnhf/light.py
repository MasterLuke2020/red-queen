"""Native Home Assistant light entities for WNHF."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DATA_ENGINE,
    DOMAIN,
    SIGNAL_REGISTRY_RELOADED,
    VERSION,
)
from .device import room_device_info
from .domain.light import Light
from .engine import WNHFEngine
from .native_execution import async_execute_canonical


async def _async_setup_entities(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up all controllable native WNHF light entities."""
    engine: WNHFEngine = hass.data[DOMAIN][DATA_ENGINE]
    house = engine._require_house()

    async_add_entities(
        [
            WNHFLightEntity(hass, engine, light)
            for light in house.enabled_lights
            if light.controllable
        ],
        update_before_add=False,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WNHF entities from a config entry."""
    await _async_setup_entities(
        hass,
        {},
        async_add_entities,
        None,
    )


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Retain compatibility with the legacy platform loader."""
    await _async_setup_entities(
        hass,
        config,
        async_add_entities,
        discovery_info,
    )


class WNHFLightEntity(LightEntity):
    """Native HA adapter for one impulse-controlled PLC light."""

    _attr_should_poll = False
    _attr_has_entity_name = False
    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        light: Light,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self.light_object = light

        object_slug = (
            light.object_id
            .removeprefix("light.")
            .replace(".", "_")
        )

        self._attr_name = f"Red Queen {light.name}"
        self._attr_unique_id = f"wnhf_{object_slug}"
        self._attr_suggested_object_id = f"wnhf_{object_slug}"
        self._attr_device_info = room_device_info(
            engine,
            light.room_id,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe directly to this light's feedback entities."""
        await super().async_added_to_hass()

        @callback
        def async_feedback_changed(event: Event) -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                set(self.light_object.state_entity_ids),
                async_feedback_changed,
            )
        )

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_REGISTRY_RELOADED,
                self._async_registry_reloaded,
            )
        )

    @callback
    def _async_registry_reloaded(self) -> None:
        """Refresh state after a registry reload."""
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return whether command and feedback entities are usable."""
        return self.engine.light_snapshot(
            self.light_object.object_id
        ).available

    @property
    def is_on(self) -> bool:
        """Return the objective PLC feedback state."""
        return self.engine.light_snapshot(
            self.light_object.object_id
        ).is_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Request ON through canonical guarded semantic execution."""
        await async_execute_canonical(
            self.hass,
            action_id="lighting.turn_on",
            object_id=self.light_object.object_id,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Request OFF through canonical guarded semantic execution."""
        await async_execute_canonical(
            self.hass,
            action_id="lighting.turn_off",
            object_id=self.light_object.object_id,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose WNHF identity and underlying adapter diagnostics."""
        snapshot = self.engine.light_snapshot(
            self.light_object.object_id
        )
        return {
            "wnhf_id": self.light_object.object_id,
            "room_id": self.light_object.room_id,
            "control_mode": "momentary_impulse",
            "command_entity_id": self.light_object.command_entity_id,
            "feedback_entity_ids": list(
                self.light_object.state_entity_ids
            ),
            "feedback_states": snapshot.feedback_states,
            "capabilities": [
                "turn_on",
                "turn_off",
                "pulse_command",
            ],
            "brightness_supported": False,
            "color_supported": False,
            "framework_version": VERSION,
            "color_mode": ColorMode.ONOFF,
        }
