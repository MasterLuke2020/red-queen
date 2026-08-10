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
from .engine import WNHFEngine


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
                {
                    self.cover_object.open_feedback_entity_id,
                    self.cover_object.closed_feedback_entity_id,
                    self.cover_object.opening_feedback_entity_id,
                    self.cover_object.closing_feedback_entity_id,
                },
                async_feedback_changed,
            )
        )

    @property
    def available(self) -> bool:
        """Return whether every required PLC feedback entity is available."""
        if not self.cover_object.enabled:
            return False

        entity_ids = (
            self.cover_object.open_feedback_entity_id,
            self.cover_object.closed_feedback_entity_id,
            self.cover_object.opening_feedback_entity_id,
            self.cover_object.closing_feedback_entity_id,
        )
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
        """Expose only objectively known end positions."""
        snapshot = self.engine.cover_snapshot(
            self.cover_object.object_id
        )
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
        await self.engine.async_cover_open(
            self.cover_object.object_id
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.engine.async_cover_close(
            self.cover_object.object_id
        )

    async def async_open_cover_tilt(self, **kwargs: Any) -> None:
        await self.engine.async_cover_blades_open(
            self.cover_object.object_id
        )

    async def async_close_cover_tilt(self, **kwargs: Any) -> None:
        await self.engine.async_cover_blades_close(
            self.cover_object.object_id
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
            "is_not_fully_open": snapshot.is_not_fully_open,
            "errors": list(snapshot.errors),
            "feedback": {
                "open": snapshot.feedback_open,
                "not_fully_open": snapshot.feedback_closed,
                "opening": snapshot.feedback_opening,
                "closing": snapshot.feedback_closing,
            },
            "capabilities": list(self.cover_object.capabilities),
            "stop_supported": False,
            "position_supported": False,
            "tilt_position_supported": False,
            "framework_version": VERSION,
        }
