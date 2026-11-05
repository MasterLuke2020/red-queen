"""Native mode selector for Red Queen Smart Living 1.1."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN
from .device import module_device_info
from .smart_living_runtime import DATA_SMART_LIVING, SIGNAL_SMART_LIVING_UPDATED

class RedQueenHouseModeSelect(SelectEntity):
    """Manual house mode, distinct from existing technical house health."""
    _attr_should_poll = False
    _attr_has_entity_name = False
    _attr_icon = "mdi:home-switch"
    _attr_options = ["home", "away", "vacation"]
    _attr_name = "Red Queen Hausmodus"
    _attr_unique_id = "wnhf_smart_living_house_mode"
    _attr_suggested_object_id = "wnhf_house_mode"

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.runtime = hass.data[DOMAIN][DATA_SMART_LIVING]
        self._attr_device_info = module_device_info(
            "smart_living", "Red Queen Smart Living",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(
            self.hass, SIGNAL_SMART_LIVING_UPDATED, self._refresh
        ))
        if self.runtime.auto_away:
            self.async_on_remove(async_track_state_change_event(
                self.hass, [self.runtime.away_entity_id], self._source_changed
            ))

    @callback
    def _source_changed(self, event: Event) -> None:
        self._refresh()

    @callback
    def _refresh(self) -> None:
        self.async_write_ha_state()

    @property
    def current_option(self) -> str:
        return self.runtime.mode

    async def async_select_option(self, option: str) -> None:
        # When auto away is enabled, setting home while the away sensor is 'on'
        # does not override the sensor. To force local home, disable auto-away.
        await self.runtime.async_set_mode(option)

    @property
    def extra_state_attributes(self) -> dict:
        report = self.runtime.snapshot()
        return {
            "manual_mode": report["manual_mode"],
            "mode_source": report["mode_source"],
            "quiet": report["quiet"],
            "automatic_away_enabled": report["automatic_away_enabled"],
        }


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([RedQueenHouseModeSelect(hass)])
