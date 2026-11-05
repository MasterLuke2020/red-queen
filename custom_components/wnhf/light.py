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
from .device import room_device_info, module_device_info
from .smart_living_runtime import DATA_SMART_LIVING
from .smart_living_logic import exposed_modes
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
        ] + [
            WNHFSmartRGBWLight(hass, source_id, name)
            for source_id, name in hass.data[DOMAIN][DATA_SMART_LIVING].rgbw_targets.items()
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


class WNHFSmartRGBWLight(LightEntity):
    """Safe Red Queen frontend for an allowlisted, already-existing HA RGBW light.

    The source integration remains owner of the underlying DALI/OPC UA commands.
    No fake color state is stored and existing WNHF impulse-light IDs are intact.
    """
    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(self, hass: HomeAssistant, source_entity_id: str, name: str) -> None:
        self.hass = hass
        self.runtime = hass.data[DOMAIN][DATA_SMART_LIVING]
        self.source_entity_id = source_entity_id
        slug = source_entity_id.removeprefix("light.")
        self._attr_name = f"Red Queen {name}"
        self._attr_unique_id = f"wnhf_rgbw_{slug}"
        self._attr_suggested_object_id = f"wnhf_rgbw_{slug}"
        self._attr_device_info = module_device_info(
            "smart_living", "Red Queen Smart Living",
        )

    @property
    def _source(self):
        return self.hass.states.get(self.source_entity_id)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        @callback
        def source_updated(event: Event) -> None:
            self.async_write_ha_state()
        self.async_on_remove(async_track_state_change_event(
            self.hass, [self.source_entity_id], source_updated,
        ))

    @property
    def available(self) -> bool:
        source = self._source
        return source is not None and source.state not in ("unknown", "unavailable")

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        source = self._source
        names = exposed_modes(source.attributes.get("supported_color_modes")) if source else set()
        result = {ColorMode(name) for name in names}
        if not result:
            result = {ColorMode.ONOFF}
        # HA forbids ONOFF/BRIGHTNESS alongside colour modes.
        if len(result) > 1:
            result.discard(ColorMode.ONOFF)
            result.discard(ColorMode.BRIGHTNESS)
        return result

    @property
    def color_mode(self) -> ColorMode | None:
        source = self._source
        if source is None:
            return None
        name = source.attributes.get("color_mode")
        if name in exposed_modes((name,)):
            try:
                return ColorMode(name)
            except ValueError:
                pass
        return ColorMode.ONOFF if self.available else None

    @property
    def is_on(self) -> bool:
        source = self._source
        return bool(source is not None and source.state == "on")

    @property
    def brightness(self) -> int | None:
        source = self._source
        value = source.attributes.get("brightness") if source else None
        return value if type(value) is int and 0 <= value <= 255 else None

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        source = self._source
        value = source.attributes.get("rgbw_color") if source else None
        if isinstance(value, (list, tuple)) and len(value) == 4:
            return tuple(value)
        return None

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        source = self._source
        value = source.attributes.get("rgb_color") if source else None
        if isinstance(value, (list, tuple)) and len(value) == 3:
            return tuple(value)
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.runtime.async_light_dispatch(
            self.source_entity_id, "turn_on", kwargs,
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.runtime.async_light_dispatch(
            self.source_entity_id, "turn_off", {},
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "source_entity_id": self.source_entity_id,
            "adapter": "ha_light_dali",
            "dispatch_scope": "accepted_not_physically_verified",
            "smart_living_mode": self.runtime.mode,
        }
