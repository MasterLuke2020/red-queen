"""Native Home Assistant lock entities for Red Queen."""

from __future__ import annotations

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DATA_ENGINE, DOMAIN, VERSION
from .device import room_device_info
from .domain.opening import Opening
from .engine import WNHFEngine
from .native_execution import async_execute_canonical


async def _async_setup_entities(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up one native lock for every configured semantic door lock."""
    engine: WNHFEngine = hass.data[DOMAIN][DATA_ENGINE]
    async_add_entities(
        [
            WNHFDoorLockEntity(hass, engine, opening)
            for opening in sorted(
                engine._require_house().enabled_openings,
                key=lambda item: (item.room_id, item.name, item.object_id),
            )
            if opening.lock is not None
        ],
        update_before_add=False,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    await _async_setup_entities(hass, {}, async_add_entities, None)


async def async_setup_platform(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    await _async_setup_entities(hass, config, async_add_entities, discovery_info)


class WNHFDoorLockEntity(LockEntity):
    """Room-associated adapter for one guarded semantic motor lock."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        opening: Opening,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self.opening_object = opening
        slug = opening.object_id.removeprefix("opening.").replace(".", "_")
        self._attr_name = f"Red Queen {opening.name} – Lock"
        self._attr_unique_id = f"wnhf_lock_{slug}"
        self._attr_suggested_object_id = f"wnhf_lock_{slug}"
        self._attr_device_info = room_device_info(engine, opening.room_id)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def async_feedback_changed(event: Event) -> None:
            self.async_write_ha_state()

        entity_ids = {
            self.opening_object.state_entity_id,
            self.opening_object.lock.feedback_entity_id,
        }
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                {entity_id for entity_id in entity_ids if entity_id},
                async_feedback_changed,
            )
        )

    @property
    def available(self) -> bool:
        return self.engine.access_object_snapshot(
            self.opening_object.object_id
        ).available

    @property
    def is_locked(self) -> bool | None:
        state = self.engine.access_object_snapshot(
            self.opening_object.object_id
        ).lock_state
        if state == "locked":
            return True
        if state == "unlocked":
            return False
        return None

    async def async_lock(self, **kwargs) -> None:
        await async_execute_canonical(
            self.hass,
            action_id="openings.lock",
            object_id=self.opening_object.object_id,
            confirmed=True,
        )

    async def async_unlock(self, **kwargs) -> None:
        await async_execute_canonical(
            self.hass,
            action_id="openings.unlock",
            object_id=self.opening_object.object_id,
            confirmed=True,
        )

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.access_object_snapshot(
            self.opening_object.object_id
        )
        return {
            "wnhf_id": self.opening_object.object_id,
            "room_id": self.opening_object.room_id,
            "normalized_lock_state": snapshot.lock_state,
            "door_closed": snapshot.is_closed,
            "explicit_confirmation_boundary": "native_lock_service_call",
            "canonical_actions": ["openings.lock", "openings.unlock"],
            "framework_version": VERSION,
        }
