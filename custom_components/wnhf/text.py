"""Message composition field – volatile text, never persisted to HA storage."""
from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import module_device_info
from .smart_living_runtime import DATA_SMART_LIVING
from .smart_living_messages import SIGNAL_COMPOSER_UPDATED


class RedQueenMessageText(TextEntity):
    _attr_should_poll = False
    _attr_has_entity_name = False
    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = 256
    _attr_name = "Red Queen Nachricht"
    _attr_icon = "mdi:message-text-outline"
    _attr_unique_id = "wnhf_smart_message_text"
    _attr_suggested_object_id = "wnhf_message_text"

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.composer = hass.data[DOMAIN][DATA_SMART_LIVING].composer
        self._attr_device_info = module_device_info(
            "smart_living", "Red Queen Smart Living",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(async_dispatcher_connect(
            self.hass, SIGNAL_COMPOSER_UPDATED, self.async_write_ha_state,
        ))

    @property
    def native_value(self) -> str:
        return self.composer.text

    async def async_set_value(self, value: str) -> None:
        self.composer.set_text(value)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([RedQueenMessageText(hass)])
