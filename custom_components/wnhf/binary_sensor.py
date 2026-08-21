"""Native binary sensors for WNHF."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import DATA_ENGINE, DOMAIN, VERSION
from .device import room_device_info
from .domain.opening import Opening
from .engine import WNHFEngine
from .entity import (
    WNHFDiagnosticEntity,
    WNHFLightingEntity,
    WNHFOpeningEntity,
    WNHFSecurityEntity,
    WNHFValidationEntity,
    WNHFHouseEntity,
)


async def _async_setup_entities(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up native WNHF binary sensors."""
    engine: WNHFEngine = hass.data[DOMAIN][DATA_ENGINE]
    house = engine._require_house()
    async_add_entities(
        [
            WNHFNativeLightingAnyOn(hass, engine),
            WNHFNativeLightingAllOff(hass, engine),
            WNHFFrameworkHealthy(hass, engine),
            WNHFNativeOpeningsAnyOpen(hass, engine),
            WNHFNativeOpeningsAllClosed(hass, engine),
            WNHFNativeSecuritySecure(hass, engine),
            WNHFNativeSecurityAlert(hass, engine),
            WNHFAccessAllAvailable(hass, engine),
            WNHFAccessAttentionRequired(hass, engine),
            WNHFRegistryValid(hass, engine),
            WNHFHouseReady(hass, engine),
            *(
                WNHFNativeOpeningState(hass, engine, opening)
                for opening in sorted(
                    house.enabled_openings,
                    key=lambda item: (
                        item.room_id,
                        item.name,
                        item.object_id,
                    ),
                )
            ),
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


class WNHFNativeLightingAnyOn(WNHFLightingEntity, BinarySensorEntity):
    """Report whether any enabled WNHF light object is on."""

    _attr_icon = "mdi:lightbulb-on"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Lighting Any On",
            "wnhf_lighting_any_on",
            "wnhf_lighting_any_on",
        )

    @property
    def is_on(self) -> bool:
        return self.engine.lighting_count_on() > 0

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "count_on": self.engine.lighting_count_on(),
                "lights_on": self.engine.lighting_names_on(),
                "light_ids_on": self.engine.lighting_ids_on(),
            }
        )
        return attrs


class WNHFNativeLightingAllOff(WNHFLightingEntity, BinarySensorEntity):
    """Report whether all enabled WNHF light objects are off."""

    _attr_icon = "mdi:lightbulb-off"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Lighting All Off",
            "wnhf_lighting_all_off",
            "wnhf_lighting_all_off",
        )

    @property
    def is_on(self) -> bool:
        return self.engine.lighting_count_on() == 0


class WNHFFrameworkHealthy(WNHFDiagnosticEntity, BinarySensorEntity):
    """Report whether the WNHF framework is operational."""

    _attr_icon = "mdi:heart-pulse"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Framework Healthy",
            "wnhf_framework_healthy",
            "wnhf_framework_healthy",
        )

    @property
    def is_on(self) -> bool:
        snapshot = self.engine.diagnostics_snapshot()
        return snapshot.health_status in {"healthy", "warning"}

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.diagnostics_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "health_status": snapshot.health_status,
                "health_score": snapshot.health_score,
                "warning_count": snapshot.warning_count,
                "warnings": list(snapshot.warnings),
            }
        )
        return attrs


class WNHFNativeOpeningsAnyOpen(WNHFOpeningEntity, BinarySensorEntity):
    """Report whether any WNHF opening is currently open."""

    _attr_icon = "mdi:door-open"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Openings Any Open",
            "wnhf_openings_any_open",
            "wnhf_openings_any_open",
        )

    @property
    def is_on(self) -> bool:
        return self.engine.opening_count_open() > 0

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "count_open": self.engine.opening_count_open(),
                "openings_open": self.engine.opening_names_open(),
                "opening_ids_open": self.engine.opening_ids_open(),
            }
        )
        return attrs


class WNHFNativeOpeningsAllClosed(WNHFOpeningEntity, BinarySensorEntity):
    """Report whether every enabled WNHF opening is closed."""

    _attr_icon = "mdi:shield-home"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Openings All Closed",
            "wnhf_openings_all_closed",
            "wnhf_openings_all_closed",
        )

    @property
    def is_on(self) -> bool:
        return self.engine.opening_count_open() == 0


class WNHFNativeOpeningState(BinarySensorEntity):
    """Expose one semantic opening on its Red Queen room device."""

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
        self._attr_name = f"Red Queen {opening.name}"
        self._attr_unique_id = f"wnhf_opening_{slug}"
        self._attr_suggested_object_id = f"wnhf_opening_{slug}"
        self._attr_device_info = room_device_info(engine, opening.room_id)
        self._attr_device_class = {
            "window": BinarySensorDeviceClass.WINDOW,
            "sliding_door": BinarySensorDeviceClass.DOOR,
            "door": BinarySensorDeviceClass.DOOR,
            "garage_door": BinarySensorDeviceClass.GARAGE_DOOR,
        }[opening.opening_type]

    @property
    def _feedback_entity_ids(self) -> set[str]:
        result = {self.opening_object.state_entity_id}
        if self.opening_object.lock is not None:
            result.add(self.opening_object.lock.feedback_entity_id)
        if self.opening_object.garage_door is not None:
            result.update(
                {
                    self.opening_object.garage_door.open_feedback_entity_id,
                    self.opening_object.garage_door.closed_feedback_entity_id,
                }
            )
        return {entity_id for entity_id in result if entity_id}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def async_feedback_changed(event: Event) -> None:
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                self._feedback_entity_ids,
                async_feedback_changed,
            )
        )

    @property
    def available(self) -> bool:
        if self.opening_object.garage_door is not None:
            garage = self.opening_object.garage_door
            entity_ids = {
                garage.open_feedback_entity_id,
                garage.closed_feedback_entity_id,
            }
        else:
            entity_ids = {self.opening_object.state_entity_id}
        entity_ids = {entity_id for entity_id in entity_ids if entity_id}
        return all(
            (state := self.hass.states.get(entity_id)) is not None
            and state.state not in {"unknown", "unavailable"}
            for entity_id in entity_ids
        ) and bool(entity_ids)

    @property
    def is_on(self) -> bool:
        return self.engine.access_object_snapshot(
            self.opening_object.object_id
        ).is_open

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.access_object_snapshot(
            self.opening_object.object_id
        )
        return {
            "wnhf_id": self.opening_object.object_id,
            "room_id": self.opening_object.room_id,
            "opening_type": self.opening_object.opening_type,
            "normalized_state": snapshot.state,
            "secure": snapshot.secure,
            "lock_state": snapshot.lock_state,
            "has_lock": snapshot.has_lock,
            "has_door_opener": snapshot.has_door_opener,
            "framework_version": VERSION,
        }


class WNHFNativeSecuritySecure(WNHFSecurityEntity, BinarySensorEntity):
    """Report whether the building is objectively secure."""

    _attr_icon = "mdi:shield-check"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Security Secure",
            "wnhf_security_secure",
            "wnhf_security_secure",
        )

    @property
    def is_on(self) -> bool:
        return self.engine.security_snapshot().secure

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.security_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "level": snapshot.level,
                "open_count": snapshot.open_count,
                "insecure_count": snapshot.insecure_count,
                "all_access_available": snapshot.all_access_available,
                "access_attention_required": (
                    snapshot.access_attention_required
                ),
                "opening_ids": list(snapshot.opening_ids),
                "opening_names": list(snapshot.opening_names),
                "insecure_ids": list(snapshot.insecure_ids),
                "insecure_names": list(snapshot.insecure_names),
            }
        )
        return attrs


class WNHFNativeSecurityAlert(WNHFSecurityEntity, BinarySensorEntity):
    """Report whether an objective security alert is active."""

    _attr_icon = "mdi:shield-alert"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Security Alert",
            "wnhf_security_alert",
            "wnhf_security_alert",
        )

    @property
    def is_on(self) -> bool:
        return self.engine.security_snapshot().alert

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.security_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "level": snapshot.level,
                "open_count": snapshot.open_count,
                "opening_ids": list(snapshot.opening_ids),
                "opening_names": list(snapshot.opening_names),
            }
        )
        return attrs



class WNHFAccessAllAvailable(WNHFSecurityEntity, BinarySensorEntity):
    """Report whether all enabled Access feedback is available."""

    _attr_icon = "mdi:access-point-check"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Access All Available",
            "wnhf_access_all_available",
            "wnhf_access_all_available",
        )

    @property
    def is_on(self) -> bool:
        return self.engine.security_snapshot().all_access_available

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.security_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "unavailable_count": snapshot.unavailable_count,
                "unavailable_ids": list(snapshot.unavailable_ids),
                "unavailable_names": list(snapshot.unavailable_names),
            }
        )
        return attrs


class WNHFAccessAttentionRequired(
    WNHFSecurityEntity,
    BinarySensorEntity,
):
    """Report whether Access runtime requires technical attention."""

    _attr_icon = "mdi:shield-alert-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Access Attention Required",
            "wnhf_access_attention_required",
            "wnhf_access_attention_required",
        )

    @property
    def is_on(self) -> bool:
        return self.engine.security_snapshot().access_attention_required

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.security_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "attention_count": snapshot.attention_count,
                "attention_ids": list(snapshot.attention_ids),
                "attention_names": list(snapshot.attention_names),
            }
        )
        return attrs


class WNHFRegistryValid(WNHFValidationEntity, BinarySensorEntity):
    """Report whether the latest full validation has no errors."""

    _attr_icon = "mdi:database-check"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Registry Valid",
            "wnhf_registry_valid",
            "wnhf_registry_valid",
        )

    @property
    def is_on(self) -> bool:
        report = self.engine.validation_snapshot()
        return report.valid if report is not None else False

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        report = self.engine.validation_snapshot()
        if report is None:
            attrs.update({"status": "pending"})
        else:
            attrs.update(
                {
                    "status": report.status,
                    "quality_score": report.quality_score,
                    "error_count": len(report.errors),
                    "warning_count": len(report.warnings),
                    "generated_at": report.generated_at.isoformat(),
                }
            )
        return attrs


class WNHFHouseReady(WNHFHouseEntity, BinarySensorEntity):
    """Report whether the house is secure and free of framework errors."""

    _attr_icon = "mdi:home-check"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen House Ready",
            "wnhf_house_ready",
            "wnhf_house_ready",
        )

    @property
    def is_on(self) -> bool:
        snapshot = self.engine.house_snapshot()
        return not snapshot.has_error and snapshot.secure

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(self.engine.house_snapshot().as_dict())
        return attrs
