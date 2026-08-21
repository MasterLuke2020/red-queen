"""Native Home Assistant buttons for Red Queen Plant Care."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_ENGINE, DOMAIN, SERVICE_EXECUTION_EXECUTE
from .engine import WNHFEngine
from .entity import WNHFPlantEntity


async def _async_setup_entities(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up one canonical watering-history button per enabled plant."""
    engine: WNHFEngine = hass.data[DOMAIN][DATA_ENGINE]
    async_add_entities(
        [
            WNHFRecordPlantWateringButton(hass, engine, plant.object_id)
            for plant in sorted(
                engine._require_house().enabled_plants,
                key=lambda item: (item.room_id, item.name, item.object_id),
            )
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
            f"Red Queen Record Watering – {plant.name}",
            f"wnhf_plant_water_{slug}",
            f"wnhf_plant_water_{slug}",
            plant.room_id,
        )

    async def async_press(self) -> None:
        """Record watering via the public canonical execution service."""
        await self.hass.services.async_call(
            DOMAIN,
            SERVICE_EXECUTION_EXECUTE,
            {
                "action_id": "plants.record_watering",
                "target": {"object_id": self.plant_id},
                "parameters": {},
                "confirmed": False,
            },
            blocking=True,
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
