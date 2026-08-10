"""Native binary sensors for WNHF."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_ENGINE, DOMAIN
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
