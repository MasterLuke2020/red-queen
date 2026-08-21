"""Native Home Assistant cover entities for WNHF."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DATA_ENGINE, DOMAIN, VERSION
from .device import room_device_info
from .domain.cover import Cover
from .domain.cover_state import CoverState
from .domain.opening import Opening
from .engine import WNHFEngine
from .native_execution import async_execute_canonical


async def _async_setup_entities(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up all native WNHF cover entities."""
    engine: WNHFEngine = hass.data[DOMAIN][DATA_ENGINE]
    house = engine._require_house()

    async_add_entities(
        [
            WNHFCoverEntity(hass, engine, cover)
            for cover in house.enabled_covers
        ]
        + [
            WNHFGarageDoorEntity(hass, engine, opening)
            for opening in house.enabled_openings
            if opening.garage_door is not None
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


class WNHFCoverEntity(CoverEntity):
    """Native Home Assistant adapter for one WNHF cover object."""

    _attr_should_poll = False
    _attr_has_entity_name = False
    _attr_device_class = CoverDeviceClass.BLIND
    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.CLOSE_TILT
    )

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        cover: Cover,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self.cover_object = cover

        object_slug = (
            cover.object_id
            .removeprefix("cover.")
            .replace(".", "_")
        )

        self._attr_name = f"Red Queen {cover.name}"
        self._attr_unique_id = f"wnhf_{object_slug}"
        self._attr_suggested_object_id = f"wnhf_{object_slug}"
        self._attr_device_info = room_device_info(
            engine,
            cover.room_id,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe directly to this cover's four PLC feedback entities."""
        await super().async_added_to_hass()

        @callback
        def async_feedback_changed(event: Event) -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                set(self.cover_object.feedback_entity_ids),
                async_feedback_changed,
            )
        )

    @property
    def available(self) -> bool:
        """Return whether every required PLC feedback entity is available."""
        if not self.cover_object.enabled:
            return False

        entity_ids = self.cover_object.direction_feedback_entity_ids
        return all(
            (state := self.hass.states.get(entity_id)) is not None
            and state.state not in {"unknown", "unavailable"}
            for entity_id in entity_ids
        )

    @property
    def is_closed(self) -> bool | None:
        """Return end-state information without mislabeling intermediate."""
        snapshot = self.engine.cover_snapshot(
            self.cover_object.object_id
        )
        if snapshot.state is CoverState.CLOSED:
            return True
        if snapshot.state is CoverState.OPEN:
            return False
        return None

    @property
    def is_opening(self) -> bool:
        return self.engine.cover_snapshot(
            self.cover_object.object_id
        ).is_opening

    @property
    def is_closing(self) -> bool:
        return self.engine.cover_snapshot(
            self.cover_object.object_id
        ).is_closing

    @property
    def current_cover_position(self) -> int | None:
        """Expose objective PLC position feedback using HA's 0=closed/100=open scale."""
        snapshot = self.engine.cover_snapshot(
            self.cover_object.object_id
        )
        if snapshot.current_position is not None:
            return snapshot.current_position
        if snapshot.is_open:
            return 100
        if snapshot.is_closed:
            return 0
        return None

    @property
    def current_cover_tilt_position(self) -> int | None:
        """No objective slat position feedback is currently available."""
        return None

    async def async_open_cover(self, **kwargs: Any) -> None:
        await async_execute_canonical(
            self.hass,
            action_id="covers.open",
            object_id=self.cover_object.object_id,
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        await async_execute_canonical(
            self.hass,
            action_id="covers.close",
            object_id=self.cover_object.object_id,
        )

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        await async_execute_canonical(
            self.hass,
            action_id="covers.blades_open",
            object_id=self.cover_object.object_id,
        )

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        await async_execute_canonical(
            self.hass,
            action_id="covers.blades_close",
            object_id=self.cover_object.object_id,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        snapshot = self.engine.cover_snapshot(
            self.cover_object.object_id
        )
        return {
            "wnhf_id": self.cover_object.object_id,
            "room_id": self.cover_object.room_id,
            "cover_type": self.cover_object.cover_type,
            "normalized_state": snapshot.state.value,
            "is_intermediate": snapshot.is_intermediate,
            "is_error": snapshot.is_error,
            "closed_percent": snapshot.closed_percent,
            "current_position": snapshot.current_position,
            "position_feedback_available": snapshot.position_available,
            "position_warnings": list(snapshot.position_warnings),
            "errors": list(snapshot.errors),
            "feedback": {
                "open": snapshot.feedback_open,
                "closed": snapshot.feedback_closed,
                "opening": snapshot.feedback_opening,
                "closing": snapshot.feedback_closing,
            },
            "capabilities": list(self.cover_object.capabilities),
            "stop_supported": False,
            "position_supported": False,
            "position_feedback_supported": bool(
                self.cover_object.closed_percent_feedback_entity_id
            ),
            "tilt_position_supported": False,
            "framework_version": VERSION,
        }


class WNHFGarageDoorEntity(CoverEntity):
    """Native room control for one guarded semantic garage door."""

    _attr_should_poll = False
    _attr_has_entity_name = False
    _attr_device_class = CoverDeviceClass.GARAGE

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        opening: Opening,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self.opening_object = opening
        self._requested_direction: str | None = None
        slug = opening.object_id.removeprefix("opening.").replace(".", "_")
        self._attr_name = f"Red Queen {opening.name}"
        self._attr_unique_id = f"wnhf_garage_{slug}"
        self._attr_suggested_object_id = f"wnhf_garage_{slug}"
        self._attr_device_info = room_device_info(engine, opening.room_id)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def async_feedback_changed(event: Event) -> None:
            self.async_write_ha_state()

        garage = self.opening_object.garage_door
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                {
                    garage.open_feedback_entity_id,
                    garage.closed_feedback_entity_id,
                    garage.toggle_command_entity_id,
                },
                async_feedback_changed,
            )
        )

    @property
    def available(self) -> bool:
        snapshot = self.engine.access_object_snapshot(
            self.opening_object.object_id
        )
        command = self.hass.states.get(
            self.opening_object.garage_door.toggle_command_entity_id
        )
        return (
            snapshot.available
            and command is not None
            and command.state != "unavailable"
        )

    @property
    def supported_features(self) -> CoverEntityFeature:
        snapshot = self.engine.access_object_snapshot(
            self.opening_object.object_id
        )
        if snapshot.state == "closed":
            return CoverEntityFeature.OPEN
        if snapshot.state == "open":
            return CoverEntityFeature.CLOSE
        return CoverEntityFeature(0)

    @property
    def is_closed(self) -> bool | None:
        snapshot = self.engine.access_object_snapshot(
            self.opening_object.object_id
        )
        if snapshot.state == "closed":
            return True
        if snapshot.state == "open":
            return False
        return None

    @property
    def is_opening(self) -> bool:
        snapshot = self.engine.access_object_snapshot(
            self.opening_object.object_id
        )
        return snapshot.state == "moving" and self._requested_direction == "open"

    @property
    def is_closing(self) -> bool:
        snapshot = self.engine.access_object_snapshot(
            self.opening_object.object_id
        )
        return snapshot.state == "moving" and self._requested_direction == "close"

    @property
    def current_cover_position(self) -> int | None:
        snapshot = self.engine.access_object_snapshot(
            self.opening_object.object_id
        )
        if snapshot.state == "closed":
            return 0
        if snapshot.state == "open":
            return 100
        return None

    async def _async_execute_direction(self, action_id: str) -> None:
        self._requested_direction = action_id.rsplit(".", 1)[-1]
        self.async_write_ha_state()
        try:
            await async_execute_canonical(
                self.hass,
                action_id=action_id,
                object_id=self.opening_object.object_id,
                confirmed=True,
            )
        finally:
            self._requested_direction = None
            self.async_write_ha_state()

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self._async_execute_direction("garage.open")

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self._async_execute_direction("garage.close")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        snapshot = self.engine.access_object_snapshot(
            self.opening_object.object_id
        )
        return {
            "wnhf_id": self.opening_object.object_id,
            "room_id": self.opening_object.room_id,
            "normalized_state": snapshot.state,
            "secure": snapshot.secure,
            "garage_elapsed_seconds": snapshot.garage_elapsed_seconds,
            "canonical_actions": ["garage.open", "garage.close"],
            "explicit_confirmation_boundary": "native_cover_service_call",
            "stop_supported": False,
            "position_feedback_supported": False,
            "framework_version": VERSION,
        }
