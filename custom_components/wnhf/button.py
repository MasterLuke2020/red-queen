"""Native Home Assistant buttons for Red Queen room functions."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DATA_ENGINE, DOMAIN, VERSION
from .device import room_device_info
from .domain.cover import Cover
from .domain.opening import Opening
from .engine import WNHFEngine
from .entity import WNHFPlantEntity
from .native_execution import async_execute_canonical
from .localization import localized


async def _async_setup_entities(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up explicit room controls backed by canonical execution."""
    engine: WNHFEngine = hass.data[DOMAIN][DATA_ENGINE]
    house = engine._require_house()
    async_add_entities(
        [
            WNHFRecordPlantWateringButton(hass, engine, plant.object_id)
            for plant in sorted(
                house.enabled_plants,
                key=lambda item: (item.room_id, item.name, item.object_id),
            )
        ]
        + [
            WNHFCoverBladeButton(hass, engine, cover, action_id)
            for cover in sorted(
                house.enabled_covers,
                key=lambda item: (item.room_id, item.name, item.object_id),
            )
            for action_id in (
                "covers.blades_open",
                "covers.blades_close",
            )
            if action_id in cover.supported_capability_ids
        ]
        + [
            WNHFDoorReleaseButton(hass, engine, opening)
            for opening in sorted(
                house.enabled_openings,
                key=lambda item: (item.room_id, item.name, item.object_id),
            )
            if opening.door_opener is not None
        ],
        update_before_add=False,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WNHF button entities from a config entry."""
    await _async_setup_entities(hass, {}, async_add_entities, None)


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


class WNHFRecordPlantWateringButton(WNHFPlantEntity, ButtonEntity):
    """Record one real manual watering event through canonical execution."""

    _attr_icon = "mdi:watering-can"
    _attr_should_poll = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        plant_id: str,
    ) -> None:
        self.plant_id = plant_id
        plant = engine._require_house().plant(plant_id)
        slug = plant_id.removeprefix("plant.").replace(".", "_")
        super().__init__(
            hass,
            engine,
            f"Red Queen {plant.name} – "
            + localized(
                hass,
                de="Gießen protokollieren",
                en="Record watering",
            ),
            f"wnhf_plant_water_{slug}",
            f"wnhf_plant_water_{slug}",
            plant.room_id,
        )

    async def async_press(self) -> None:
        """Record watering via the public canonical execution service."""
        await async_execute_canonical(
            self.hass,
            action_id="plants.record_watering",
            object_id=self.plant_id,
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Expose the semantic target and current care summary."""
        attrs = super().extra_state_attributes
        snapshot = self.engine.plant_care_snapshot(self.plant_id).as_dict()
        attrs.update(
            {
                "plant_id": self.plant_id,
                "last_watered_at": snapshot["last_watered_at"],
                "due_at": snapshot["due_at"],
                "watering_count": snapshot["watering_count"],
                "records_history_only": True,
                "physical_watering_claimed": False,
            }
        )
        return attrs


class WNHFCoverBladeButton(ButtonEntity):
    """Explicit blade-open or blade-close control on a room device."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        cover: Cover,
        action_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self.cover_object = cover
        self.action_id = action_id
        direction = "open" if action_id.endswith("_open") else "close"
        label = (
            localized(hass, de="Lamellen öffnen", en="Blades open")
            if direction == "open"
            else localized(hass, de="Lamellen schließen", en="Blades close")
        )
        slug = cover.object_id.removeprefix("cover.").replace(".", "_")
        self._attr_name = f"Red Queen {cover.name} – {label}"
        self._attr_unique_id = f"wnhf_blades_{direction}_{slug}"
        self._attr_suggested_object_id = f"wnhf_blades_{direction}_{slug}"
        self._attr_device_info = room_device_info(engine, cover.room_id)
        self._attr_icon = (
            "mdi:blinds-open" if direction == "open" else "mdi:blinds"
        )

    async def async_added_to_hass(self) -> None:
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
        snapshot = self.engine.cover_snapshot(self.cover_object.object_id)
        command_id = (
            self.cover_object.blades_open_command_entity_id
            if self.action_id.endswith("_open")
            else self.cover_object.blades_close_command_entity_id
        )
        if not command_id:
            return False
        command = self.hass.states.get(command_id)
        return (
            not snapshot.is_moving
            and not snapshot.is_error
            and command is not None
            and command.state != "unavailable"
        )

    async def async_press(self) -> None:
        await async_execute_canonical(
            self.hass,
            action_id=self.action_id,
            object_id=self.cover_object.object_id,
        )

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "wnhf_id": self.cover_object.object_id,
            "room_id": self.cover_object.room_id,
            "canonical_action": self.action_id,
            "verification_scope": "dispatch",
            "blade_position_feedback_available": False,
            "framework_version": VERSION,
        }


class WNHFDoorReleaseButton(ButtonEntity):
    """Confirmed electric door-release control on a room device."""

    _attr_should_poll = False
    _attr_has_entity_name = False
    _attr_icon = "mdi:door-open"

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
        self._attr_name = (
            f"Red Queen {opening.name} – "
            + localized(hass, de="Türöffner", en="Door release")
        )
        self._attr_unique_id = f"wnhf_door_release_{slug}"
        self._attr_suggested_object_id = f"wnhf_door_release_{slug}"
        self._attr_device_info = room_device_info(engine, opening.room_id)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def async_feedback_changed(event: Event) -> None:
            self.async_write_ha_state()

        entity_ids = {
            self.opening_object.state_entity_id,
            self.opening_object.door_opener.command_entity_id,
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
        snapshot = self.engine.access_object_snapshot(
            self.opening_object.object_id
        )
        command = self.hass.states.get(
            self.opening_object.door_opener.command_entity_id
        )
        return (
            snapshot.available
            and snapshot.is_closed
            and command is not None
            and command.state != "unavailable"
        )

    async def async_press(self) -> None:
        await async_execute_canonical(
            self.hass,
            action_id="openings.release",
            object_id=self.opening_object.object_id,
            confirmed=True,
        )

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "wnhf_id": self.opening_object.object_id,
            "room_id": self.opening_object.room_id,
            "canonical_action": "openings.release",
            "explicit_confirmation_boundary": "native_button_press",
            "verification_scope": "dispatch",
            "physical_opening_claimed": False,
            "framework_version": VERSION,
        }
