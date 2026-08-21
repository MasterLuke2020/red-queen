"""Native sensors for WNHF."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DATA_ENGINE,
    DOMAIN,
    EXECUTION_AUDIT_LIMIT,
    RELEASE_CHANNEL,
    RELEASE_PHASE,
    VERSION,
)
from .engine import WNHFEngine
from .entity import (
    WNHFDiagnosticEntity,
    WNHFLightingEntity,
    WNHFOpeningEntity,
    WNHFSecurityEntity,
    WNHFValidationEntity,
    WNHFHouseEntity,
    WNHFCapabilityEntity,
    WNHFRuleEntity,
    WNHFContextEntity,
    WNHFPolicyEntity,
    WNHFDecisionEntity,
    WNHFExecutionEntity,
    WNHFPlantEntity,
)


async def _async_setup_entities(
    hass: HomeAssistant,
    config: dict,
    async_add_entities: AddEntitiesCallback,
    discovery_info: dict | None = None,
) -> None:
    """Set up native WNHF sensors."""
    engine: WNHFEngine = hass.data[DOMAIN][DATA_ENGINE]
    async_add_entities(
        [
            WNHFNativeLightingCountOn(hass, engine),
            WNHFNativeLightingStatus(hass, engine),
            WNHFNativeLightingMessage(hass, engine),
            WNHFFrameworkVersion(hass, engine),
            WNHFRuntimeStatus(hass, engine),
            WNHFHealthScore(hass, engine),
            WNHFRegistryStatus(hass, engine),
            WNHFModuleStatus(hass, engine),
            WNHFCapabilities(hass, engine),
            WNHFRegistryLoadTime(hass, engine),
            WNHFLastAction(hass, engine),
            WNHFLastActionTime(hass, engine),
            WNHFPerformanceSummary(hass, engine),
            WNHFNativeOpeningsCountOpen(hass, engine),
            WNHFNativeOpeningsStatus(hass, engine),
            WNHFNativeOpeningsMessage(hass, engine),
            WNHFNativeSecurityLevel(hass, engine),
            WNHFNativeSecurityMessage(hass, engine),
            WNHFNativeSecurityOpenings(hass, engine),
            WNHFRegistryValidationStatus(hass, engine),
            WNHFRegistryValidationIssues(hass, engine),
            WNHFQualityScore(hass, engine),
            WNHFHouseStatus(hass, engine),
            WNHFHouseMessage(hass, engine),
            WNHFHouseActivity(hass, engine),
            WNHFCapabilitiesStatus(hass, engine),
            WNHFCapabilitiesSupported(hass, engine),
            WNHFRuleEngineStatus(hass, engine),
            WNHFRulesLoaded(hass, engine),
            WNHFRulesMatched(hass, engine),
            WNHFContext(hass, engine),
            WNHFContextMessage(hass, engine),
            WNHFContextConfidence(hass, engine),
            WNHFActivityScore(hass, engine),
            WNHFAttentionScore(hass, engine),
            WNHFPolicyMode(hass, engine),
            WNHFPoliciesLoaded(hass, engine),
            WNHFPolicyLastDecision(hass, engine),
            WNHFDecisionsLoaded(hass, engine),
            WNHFDecisionLastStatus(hass, engine),
            WNHFDecisionLastAction(hass, engine),
            WNHFRegistryRecoveryStatus(hass, engine),
            WNHFExecutionLastStatus(hass, engine),
            WNHFExecutionLastSteps(hass, engine),
            WNHFExecutionLastTransaction(hass, engine),
            WNHFExecutionAuditCount(hass, engine),
            WNHFPublicExecutionLastStatus(hass, engine),
            WNHFMultiStepPlanLastStatus(hass, engine),
            WNHFMultiStepSimulationLastStatus(hass, engine),
            WNHFGenericTransactionLastState(hass, engine),
            WNHFRealStepLastState(hass, engine),
            WNHFSequentialRoomLastState(hass, engine),
            WNHFHouseExecutionLastState(hass, engine),
            WNHFTransactionLockState(hass, engine),
            WNHFTransactionQueueState(hass, engine),
            WNHFSystemReadiness(hass, engine),
            WNHFReleaseScope(hass, engine),
            WNHFReleasePhase(hass, engine),
            *(
                WNHFPlantCareStatus(hass, engine, plant.object_id)
                for plant in sorted(
                    engine._require_house().enabled_plants,
                    key=lambda item: (item.room_id, item.name, item.object_id),
                )
            ),
        ],
        update_before_add=False,
    )


class WNHFPlantCareStatus(WNHFPlantEntity, SensorEntity):
    """Dashboard-ready care status for one semantic plant."""

    _attr_icon = "mdi:sprout"

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
            f"Red Queen Plant Care – {plant.name}",
            f"wnhf_plant_care_{slug}",
            f"wnhf_plant_care_{slug}",
            plant.room_id,
        )

    @property
    def native_value(self) -> str:
        return self.engine.plant_care_snapshot(self.plant_id).status

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(self.engine.plant_care_snapshot(self.plant_id).as_dict())
        return attrs


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


class WNHFNativeLightingCountOn(WNHFLightingEntity, SensorEntity):
    """Number of enabled WNHF light objects currently reporting on."""

    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "lights"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Lighting Count On",
            "wnhf_lighting_count_on",
            "wnhf_lighting_count_on",
        )

    @property
    def native_value(self) -> int:
        return self.engine.lighting_count_on()


class WNHFNativeLightingStatus(WNHFLightingEntity, SensorEntity):
    """Compact native WNHF lighting status."""

    _attr_icon = "mdi:home-lightbulb"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Lighting Status",
            "wnhf_lighting_status",
            "wnhf_lighting_status",
        )

    @property
    def native_value(self) -> str:
        return (
            "all_off"
            if self.engine.lighting_count_on() == 0
            else "lights_on"
        )


class WNHFNativeLightingMessage(WNHFLightingEntity, SensorEntity):
    """Human-readable native lighting status."""

    _attr_icon = "mdi:message-text"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Lighting Message",
            "wnhf_lighting_message",
            "wnhf_lighting_message",
        )

    @property
    def native_value(self) -> str:
        count = self.engine.lighting_count_on()
        if count == 0:
            return "Alle Lichter sind ausgeschaltet."
        if count == 1:
            return "1 Licht ist eingeschaltet."
        return f"{count} Lichter sind eingeschaltet."

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "lights_on": self.engine.lighting_names_on(),
                "light_ids_on": self.engine.lighting_ids_on(),
            }
        )
        return attrs


class WNHFFrameworkVersion(WNHFDiagnosticEntity, SensorEntity):
    """Expose the active WNHF framework version."""

    _attr_icon = "mdi:package-variant-closed"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Framework Version",
            "wnhf_framework_version",
            "wnhf_framework_version",
        )

    @property
    def native_value(self) -> str:
        return self.engine.diagnostics_snapshot().framework_version


class WNHFRuntimeStatus(WNHFDiagnosticEntity, SensorEntity):
    """Expose the WNHF runtime status."""

    _attr_icon = "mdi:engine"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Runtime Status",
            "wnhf_runtime_status",
            "wnhf_runtime_status",
        )

    @property
    def native_value(self) -> str:
        return self.engine.diagnostics_snapshot().runtime_status

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.diagnostics_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "house_id": snapshot.house_id,
                "house_name": snapshot.house_name,
                "registry_loaded_at": (
                    snapshot.registry_loaded_at.isoformat()
                    if snapshot.registry_loaded_at is not None
                    else None
                ),
            }
        )
        return attrs


class WNHFHealthScore(WNHFDiagnosticEntity, SensorEntity):
    """Expose the calculated framework health score."""

    _attr_icon = "mdi:heart-flash"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Health Score",
            "wnhf_health_score",
            "wnhf_health_score",
        )

    @property
    def native_value(self) -> int:
        return self.engine.diagnostics_snapshot().health_score

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.diagnostics_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "health_status": snapshot.health_status,
                "warning_count": snapshot.warning_count,
                "warnings": list(snapshot.warnings),
                "calculation": "100 minus 2 points per registry warning",
            }
        )
        return attrs


class WNHFRegistryStatus(WNHFDiagnosticEntity, SensorEntity):
    """Expose registry health and object counts."""

    _attr_icon = "mdi:database-check"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Registry Status",
            "wnhf_registry_status",
            "wnhf_registry_status",
        )

    @property
    def native_value(self) -> str:
        return self.engine.diagnostics_snapshot().registry_status

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.diagnostics_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "house_id": snapshot.house_id,
                "house_name": snapshot.house_name,
                "rooms": snapshot.room_count,
                "lights": snapshot.light_count,
                "openings": snapshot.opening_count,
                "covers": snapshot.cover_count,
                "cover_states": self.engine.cover_state_summary(),
                "cover_errors": [
                    item.as_dict()
                    for item in self.engine.covers_error()
                ],
                "enabled_lights": snapshot.enabled_light_count,
                "controllable_lights": snapshot.controllable_light_count,
                "warnings": list(snapshot.warnings),
                "registry_load_ms": snapshot.registry_load_ms,
                "registry_loaded_at": (
                    snapshot.registry_loaded_at.isoformat()
                    if snapshot.registry_loaded_at is not None
                    else None
                ),
            }
        )
        return attrs


class WNHFModuleStatus(WNHFDiagnosticEntity, SensorEntity):
    """Expose installed and running WNHF modules."""

    _attr_icon = "mdi:view-module"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Module Status",
            "wnhf_module_status",
            "wnhf_module_status",
        )

    @property
    def native_value(self) -> int:
        snapshot = self.engine.diagnostics_snapshot()
        return sum(
            1 for module in snapshot.modules.values()
            if module.status == "running"
        )

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.diagnostics_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "module_count": len(snapshot.modules),
                "modules": snapshot.module_attributes(),
            }
        )
        return attrs


class WNHFCapabilities(WNHFDiagnosticEntity, SensorEntity):
    """Expose active WNHF framework capabilities."""

    _attr_icon = "mdi:format-list-checks"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Capabilities",
            "wnhf_capabilities",
            "wnhf_capabilities",
        )

    @property
    def native_value(self) -> int:
        snapshot = self.engine.diagnostics_snapshot()
        return sum(1 for active in snapshot.capabilities.values() if active)

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.diagnostics_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "capabilities": snapshot.capabilities,
                "active": [
                    capability
                    for capability, active in snapshot.capabilities.items()
                    if active
                ],
            }
        )
        return attrs


class WNHFRegistryLoadTime(WNHFDiagnosticEntity, SensorEntity):
    """Expose the latest registry loading duration."""

    _attr_icon = "mdi:timer-sand"
    _attr_native_unit_of_measurement = "ms"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Registry Load Time",
            "wnhf_registry_load_time",
            "wnhf_registry_load_time",
        )

    @property
    def native_value(self) -> float | None:
        return self.engine.registry_load_ms


class WNHFLastAction(WNHFDiagnosticEntity, SensorEntity):
    """Expose the last measured WNHF action."""

    _attr_icon = "mdi:play-speed"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Last Action",
            "wnhf_last_action",
            "wnhf_last_action",
        )

    @property
    def native_value(self) -> str:
        metric = self.engine.performance.last_action
        return metric.action_id if metric is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        metric = self.engine.performance.last_action
        if metric is not None:
            attrs.update(metric.as_dict())
        return attrs


class WNHFLastActionTime(WNHFDiagnosticEntity, SensorEntity):
    """Expose the runtime of the latest WNHF action."""

    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = "ms"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Last Action Time",
            "wnhf_last_action_time",
            "wnhf_last_action_time",
        )

    @property
    def native_value(self) -> float | None:
        metric = self.engine.performance.last_action
        return metric.last_ms if metric is not None else None


class WNHFPerformanceSummary(WNHFDiagnosticEntity, SensorEntity):
    """Expose performance metrics for all measured WNHF actions."""

    _attr_icon = "mdi:speedometer"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Performance Summary",
            "wnhf_performance_summary",
            "wnhf_performance_summary",
        )

    @property
    def native_value(self) -> int:
        return sum(
            metric.calls
            for metric in self.engine.performance.actions.values()
        )

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "actions": self.engine.performance.as_dict(),
                "measured_action_count": len(
                    self.engine.performance.actions
                ),
            }
        )
        return attrs


class WNHFNativeOpeningsCountOpen(WNHFOpeningEntity, SensorEntity):
    """Expose the number of open WNHF openings."""

    _attr_icon = "mdi:counter"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Openings Count Open",
            "wnhf_openings_count_open",
            "wnhf_openings_count_open",
        )

    @property
    def native_value(self) -> int:
        return self.engine.opening_count_open()


class WNHFNativeOpeningsStatus(WNHFOpeningEntity, SensorEntity):
    """Expose a compact openings status."""

    _attr_icon = "mdi:door"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Openings Status",
            "wnhf_openings_status",
            "wnhf_openings_status",
        )

    @property
    def native_value(self) -> str:
        return (
            "all_closed"
            if self.engine.opening_count_open() == 0
            else "openings_open"
        )


class WNHFNativeOpeningsMessage(WNHFOpeningEntity, SensorEntity):
    """Expose a human-readable openings summary."""

    _attr_icon = "mdi:message-alert-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Openings Message",
            "wnhf_openings_message",
            "wnhf_openings_message",
        )

    @property
    def native_value(self) -> str:
        """Return a short, stable HA-safe state."""
        return "closed" if self.engine.opening_count_open() == 0 else "open"

    @property
    def extra_state_attributes(self) -> dict:
        count = self.engine.opening_count_open()
        names = self.engine.opening_names_open()
        attrs = super().extra_state_attributes

        if count == 0:
            full_message = "Alle Öffnungen sind geschlossen."
        elif count == 1:
            full_message = f"1 Öffnung ist offen: {names[0]}."
        else:
            full_message = (
                f"{count} Öffnungen sind offen: {', '.join(names)}."
            )

        attrs.update(
            {
                "open_count": count,
                "openings_open": names,
                "opening_ids_open": self.engine.opening_ids_open(),
                "full_message": full_message,
            }
        )
        return attrs


class WNHFNativeSecurityLevel(WNHFSecurityEntity, SensorEntity):
    """Expose the objective WNHF security level."""

    _attr_icon = "mdi:shield-home"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Security Level",
            "wnhf_security_level",
            "wnhf_security_level",
        )

    @property
    def native_value(self) -> str:
        return self.engine.security_snapshot().level

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.security_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "supported_levels": ["secure", "info", "warning", "critical"],
                "open_count": snapshot.open_count,
            }
        )
        return attrs


class WNHFNativeSecurityMessage(WNHFSecurityEntity, SensorEntity):
    """Expose the human-readable security summary."""

    _attr_icon = "mdi:message-alert-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Security Message",
            "wnhf_security_message",
            "wnhf_security_message",
        )

    @property
    def native_value(self) -> str:
        """Return a short, stable HA-safe security state."""
        snapshot = self.engine.security_snapshot()

        if snapshot.unavailable_count:
            return "unavailable"
        if snapshot.attention_count:
            return "attention"
        if snapshot.secure:
            return "secure"
        return "insecure"

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.security_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "level": snapshot.level,
                "secure": snapshot.secure,
                "all_access_available": snapshot.all_access_available,
                "access_attention_required": (
                    snapshot.access_attention_required
                ),
                "open_count": snapshot.open_count,
                "insecure_count": snapshot.insecure_count,
                "unavailable_count": snapshot.unavailable_count,
                "attention_count": snapshot.attention_count,
                "opening_ids": list(snapshot.opening_ids),
                "opening_names": list(snapshot.opening_names),
                "insecure_ids": list(snapshot.insecure_ids),
                "insecure_names": list(snapshot.insecure_names),
                "unavailable_ids": list(snapshot.unavailable_ids),
                "unavailable_names": list(snapshot.unavailable_names),
                "attention_ids": list(snapshot.attention_ids),
                "attention_names": list(snapshot.attention_names),
                "full_message": snapshot.message,
            }
        )
        return attrs


class WNHFNativeSecurityOpenings(WNHFSecurityEntity, SensorEntity):
    """Expose the number and stable IDs of security-relevant open objects."""

    _attr_icon = "mdi:format-list-bulleted"
    _attr_native_unit_of_measurement = "openings"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Security Openings",
            "wnhf_security_openings",
            "wnhf_security_openings",
        )

    @property
    def native_value(self) -> int:
        return self.engine.security_snapshot().open_count

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.security_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "opening_ids": list(snapshot.opening_ids),
                "opening_names": list(snapshot.opening_names),
            }
        )
        return attrs


class WNHFRegistryValidationStatus(WNHFValidationEntity, SensorEntity):
    """Expose healthy, warning, error or pending."""

    _attr_icon = "mdi:clipboard-check-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Registry Validation Status",
            "wnhf_registry_validation_status",
            "wnhf_registry_validation_status",
        )

    @property
    def native_value(self) -> str:
        report = self.engine.validation_snapshot()
        return report.status if report is not None else "pending"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        report = self.engine.validation_snapshot()
        if report is not None:
            attrs.update(report.as_dict())
        return attrs


class WNHFRegistryValidationIssues(WNHFValidationEntity, SensorEntity):
    """Expose the number of errors and warnings."""

    _attr_icon = "mdi:alert-circle-check-outline"
    _attr_native_unit_of_measurement = "issues"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Registry Validation Issues",
            "wnhf_registry_validation_issues",
            "wnhf_registry_validation_issues",
        )

    @property
    def native_value(self) -> int:
        report = self.engine.validation_snapshot()
        if report is None:
            return 0
        return len(report.errors) + len(report.warnings)

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        report = self.engine.validation_snapshot()
        if report is not None:
            attrs.update(
                {
                    "errors": [item.as_dict() for item in report.errors],
                    "warnings": [item.as_dict() for item in report.warnings],
                    "info": [item.as_dict() for item in report.info],
                    "checks": report.checks,
                    "summary": report.summary,
                    "generated_at": report.generated_at.isoformat(),
                }
            )
        return attrs


class WNHFQualityScore(WNHFValidationEntity, SensorEntity):
    """Expose the validator quality score."""

    _attr_icon = "mdi:quality-high"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Quality Score",
            "wnhf_quality_score",
            "wnhf_quality_score",
        )

    @property
    def native_value(self) -> int:
        report = self.engine.validation_snapshot()
        return report.quality_score if report is not None else 0

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        report = self.engine.validation_snapshot()
        if report is not None:
            attrs.update(
                {
                    "status": report.status,
                    "error_count": len(report.errors),
                    "warning_count": len(report.warnings),
                    "calculation": (
                        "100 minus 15 points per error and "
                        "2 points per warning"
                    ),
                }
            )
        return attrs


class WNHFHouseStatus(WNHFHouseEntity, SensorEntity):
    """Expose the normalized overall house state."""

    _attr_icon = "mdi:home-analytics"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen House Status",
            "wnhf_house_status",
            "wnhf_house_status",
        )

    @property
    def native_value(self) -> str:
        return self.engine.house_snapshot().state.value

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(self.engine.house_snapshot().as_dict())
        return attrs


class WNHFHouseMessage(WNHFHouseEntity, SensorEntity):
    """Expose one prioritized human-readable building message."""

    _attr_icon = "mdi:home-alert-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen House Message",
            "wnhf_house_message",
            "wnhf_house_message",
        )

    @property
    def native_value(self) -> str:
        """Return the bounded semantic house state as HA state."""
        return self.engine.house_snapshot().state.value

    @property
    def extra_state_attributes(self) -> dict:
        snapshot = self.engine.house_snapshot()
        attrs = super().extra_state_attributes
        attrs.update(snapshot.as_dict())
        attrs["full_message"] = snapshot.message
        return attrs


class WNHFHouseActivity(WNHFHouseEntity, SensorEntity):
    """Expose the number of active visible building objects."""

    _attr_icon = "mdi:home-lightning-bolt-outline"
    _attr_native_unit_of_measurement = "objects"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen House Activity",
            "wnhf_house_activity",
            "wnhf_house_activity",
        )

    @property
    def native_value(self) -> int:
        snapshot = self.engine.house_snapshot()
        return snapshot.lights_on_count + snapshot.covers_moving_count

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(self.engine.house_snapshot().as_dict())
        return attrs


class WNHFCapabilitiesStatus(WNHFCapabilityEntity, SensorEntity):
    """Expose the worst state across all registered capabilities."""

    _attr_icon = "mdi:puzzle-check-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Capabilities Status",
            "wnhf_capabilities_status",
            "wnhf_capabilities_status",
        )

    @property
    def native_value(self) -> str:
        snapshots = self.engine.providers.snapshots().values()
        states = {item.state.value for item in snapshots}
        for state in ("unavailable", "degraded", "healthy"):
            if state in states:
                return state
        return "unsupported"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "capabilities": self.engine.capabilities_snapshot(),
                "providers": list(self.engine.providers.provider_ids()),
            }
        )
        return attrs


class WNHFCapabilitiesSupported(WNHFCapabilityEntity, SensorEntity):
    """Expose the number of supported registered capabilities."""

    _attr_icon = "mdi:puzzle-outline"
    _attr_native_unit_of_measurement = "capabilities"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Capabilities Supported",
            "wnhf_capabilities_supported",
            "wnhf_capabilities_supported",
        )

    @property
    def native_value(self) -> int:
        return sum(
            1
            for item in self.engine.providers.snapshots().values()
            if item.supported
        )

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        snapshots = self.engine.providers.snapshots()
        attrs.update(
            {
                "supported": [
                    key for key, item in snapshots.items() if item.supported
                ],
                "available": [
                    key for key, item in snapshots.items() if item.available
                ],
                "healthy": [
                    key for key, item in snapshots.items() if item.healthy
                ],
                "unsupported": [
                    key for key, item in snapshots.items()
                    if not item.supported
                ],
            }
        )
        return attrs


class WNHFRuleEngineStatus(WNHFRuleEntity, SensorEntity):
    """Expose the current rule-engine status."""

    _attr_icon = "mdi:state-machine"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Rule Engine Status",
            "wnhf_rule_engine_status",
            "wnhf_rule_engine_status",
        )

    @property
    def native_value(self) -> str:
        return self.engine.evaluate_rules().status

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(self.engine.evaluate_rules().as_dict())
        return attrs


class WNHFRulesLoaded(WNHFRuleEntity, SensorEntity):
    """Expose the number of loaded declarative rules."""

    _attr_icon = "mdi:file-tree-outline"
    _attr_native_unit_of_measurement = "rules"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Rules Loaded",
            "wnhf_rules_loaded",
            "wnhf_rules_loaded",
        )

    @property
    def native_value(self) -> int:
        return len(self.engine.rule_registry.rules)

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(self.engine.rule_registry.as_dict())
        return attrs


class WNHFRulesMatched(WNHFRuleEntity, SensorEntity):
    """Expose the number of rules matching the current facts."""

    _attr_icon = "mdi:check-decagram-outline"
    _attr_native_unit_of_measurement = "rules"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Rules Matched",
            "wnhf_rules_matched",
            "wnhf_rules_matched",
        )

    @property
    def native_value(self) -> int:
        return self.engine.evaluate_rules().matched_count

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        snapshot = self.engine.evaluate_rules()
        attrs.update(
            {
                "status": snapshot.status,
                "winner": (
                    snapshot.winner.as_dict()
                    if snapshot.winner is not None
                    else None
                ),
                "winner_state": snapshot.winner_state,
                "matches": [item.as_dict() for item in snapshot.matches],
            }
        )
        return attrs


class WNHFContext(WNHFContextEntity, SensorEntity):
    """Expose the selected semantic context."""

    _attr_icon = "mdi:brain"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Context",
            "wnhf_context",
            "wnhf_context",
        )

    @property
    def native_value(self) -> str:
        return self.engine.context_snapshot().state

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        snapshot = self.engine.context_snapshot()
        # The full context snapshot intentionally remains available through
        # wnhf.context_snapshot. A Home Assistant entity must keep recorder
        # attributes bounded; rule facts and full match payloads can exceed
        # Home Assistant's 16 KiB state-attribute limit.
        attrs.update(
            {
                "generated_at": snapshot.generated_at.isoformat(),
                "state": snapshot.state,
                "message": snapshot.message,
                "confidence": snapshot.confidence,
                "confidence_percent": snapshot.confidence_percent,
                "priority": snapshot.priority,
                "rule_id": snapshot.rule_id,
                "rule_name": snapshot.rule_name,
                "source": snapshot.source,
                "scores": snapshot.scores.as_dict(),
                "reasons": list(snapshot.reasons),
                "matched_count": snapshot.rule_snapshot.matched_count,
                "registry_warnings": list(
                    snapshot.rule_snapshot.registry_warnings
                ),
                "full_snapshot_service": "wnhf.context_snapshot",
            }
        )
        return attrs


class WNHFContextMessage(WNHFContextEntity, SensorEntity):
    """Expose the selected context message."""

    _attr_icon = "mdi:message-processing-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Context Message",
            "wnhf_context_message",
            "wnhf_context_message",
        )

    @property
    def native_value(self) -> str:
        """Return a bounded machine-readable HA state."""
        snapshot = self.engine.context_snapshot()
        if snapshot.state in {
            "ready",
            "activity",
            "attention",
            "error",
            "unknown",
        }:
            return snapshot.state
        return "custom"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        snapshot = self.engine.context_snapshot()
        attrs.update(
            {
                "state": snapshot.state,
                "full_message": snapshot.message,
                "reasons": list(snapshot.reasons),
                "rule_id": snapshot.rule_id,
                "confidence_percent": snapshot.confidence_percent,
            }
        )
        return attrs


class WNHFContextConfidence(WNHFContextEntity, SensorEntity):
    """Expose confidence of the winning context rule."""

    _attr_icon = "mdi:percent-circle-outline"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Context Confidence",
            "wnhf_context_confidence",
            "wnhf_context_confidence",
        )

    @property
    def native_value(self) -> int:
        return self.engine.context_snapshot().confidence_percent

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        snapshot = self.engine.context_snapshot()
        attrs.update(
            {
                "context": snapshot.state,
                "rule_id": snapshot.rule_id,
                "rule_name": snapshot.rule_name,
                "priority": snapshot.priority,
                "source": snapshot.source,
            }
        )
        return attrs


class WNHFActivityScore(WNHFContextEntity, SensorEntity):
    """Expose deterministic visible-activity score."""

    _attr_icon = "mdi:run-fast"
    _attr_native_unit_of_measurement = "points"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Activity Score",
            "wnhf_activity_score",
            "wnhf_activity_score",
        )

    @property
    def native_value(self) -> int:
        return self.engine.context_scores().activity

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        snapshot = self.engine.house_snapshot()
        attrs.update(
            {
                "formula": "lights_on + covers_moving * 2",
                "lights_on": snapshot.lights_on_count,
                "covers_moving": snapshot.covers_moving_count,
            }
        )
        return attrs


class WNHFAttentionScore(WNHFContextEntity, SensorEntity):
    """Expose deterministic attention score."""

    _attr_icon = "mdi:alert-decagram-outline"
    _attr_native_unit_of_measurement = "points"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Attention Score",
            "wnhf_attention_score",
            "wnhf_attention_score",
        )

    @property
    def native_value(self) -> int:
        return self.engine.context_scores().attention

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        snapshot = self.engine.house_snapshot()
        attrs.update(
            {
                "formula": "openings_open * 3 + cover_errors * 5",
                "openings_open": snapshot.openings_open_count,
                "cover_errors": snapshot.covers_error_count,
            }
        )
        return attrs


class WNHFPolicyMode(WNHFPolicyEntity, SensorEntity):
    """Expose off, monitor or enforce."""

    _attr_icon = "mdi:shield-cog-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Policy Mode",
            "wnhf_policy_mode",
            "wnhf_policy_mode",
        )

    @property
    def native_value(self) -> str:
        return self.engine.policy_registry.mode.value

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "meaning": {
                    "off": "No policy blocks anything.",
                    "monitor": "Decisions are calculated but never block.",
                    "enforce": "Calculated decisions are effective.",
                },
                "recommended_initial_mode": "monitor",
            }
        )
        return attrs


class WNHFPoliciesLoaded(WNHFPolicyEntity, SensorEntity):
    """Expose number of configured policies."""

    _attr_icon = "mdi:file-document-multiple-outline"
    _attr_native_unit_of_measurement = "policies"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Policies Loaded",
            "wnhf_policies_loaded",
            "wnhf_policies_loaded",
        )

    @property
    def native_value(self) -> int:
        return len(self.engine.policy_registry.policies)

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(self.engine.policy_registry.as_dict())
        return attrs


class WNHFPolicyLastDecision(WNHFPolicyEntity, SensorEntity):
    """Expose the effective result of the last explicit policy check."""

    _attr_icon = "mdi:shield-check-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Policy Last Decision",
            "wnhf_policy_last_decision",
            "wnhf_policy_last_decision",
        )

    @property
    def native_value(self) -> str:
        decision = self.engine.last_policy_decision
        return decision.effective.value if decision is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        decision = self.engine.last_policy_decision
        if decision is not None:
            attrs.update(decision.as_dict())
        return attrs


class WNHFDecisionsLoaded(WNHFDecisionEntity, SensorEntity):
    """Expose number of configured decisions."""

    _attr_icon = "mdi:source-branch"
    _attr_native_unit_of_measurement = "decisions"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Decisions Loaded",
            "wnhf_decisions_loaded",
            "wnhf_decisions_loaded",
        )

    @property
    def native_value(self) -> int:
        return len(self.engine.decision_registry.decisions)

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(self.engine.decision_registry.as_dict())
        return attrs


class WNHFDecisionLastStatus(WNHFDecisionEntity, SensorEntity):
    """Expose last explicitly evaluated decision status."""

    _attr_icon = "mdi:account-question-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Decision Last Status",
            "wnhf_decision_last_status",
            "wnhf_decision_last_status",
        )

    @property
    def native_value(self) -> str:
        result = self.engine.last_decision_result
        return result.status.value if result is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        result = self.engine.last_decision_result
        if result is not None:
            attrs.update(result.as_dict())
        return attrs


class WNHFDecisionLastAction(WNHFDecisionEntity, SensorEntity):
    """Expose semantic action of the last evaluated decision."""

    _attr_icon = "mdi:gesture-tap-button"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Decision Last Action",
            "wnhf_decision_last_action",
            "wnhf_decision_last_action",
        )

    @property
    def native_value(self) -> str:
        result = self.engine.last_decision_result
        if result is None or result.action is None:
            return "none"
        return result.action

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        result = self.engine.last_decision_result
        if result is not None:
            attrs.update(
                {
                    "decision_id": result.decision_id,
                    "status": result.status.value,
                    "target": result.target,
                    "recommended": result.recommended,
                    "policy_allowed": result.policy_allowed,
                    "executable": result.executable,
                    "reason": result.reason,
                }
            )
        return attrs


class WNHFRegistryRecoveryStatus(WNHFDiagnosticEntity, SensorEntity):
    """Expose registry recovery and safe-mode status."""

    _attr_icon = "mdi:lifebuoy"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Registry Recovery Status",
            "wnhf_registry_recovery_status",
            "wnhf_registry_recovery_status",
        )

    @property
    def native_value(self) -> str:
        return self.engine.registry_recovery_report()["status"]

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(self.engine.registry_recovery_report())
        return attrs


class WNHFExecutionLastStatus(WNHFExecutionEntity, SensorEntity):
    """Expose status of the latest dry-run plan."""

    _attr_icon = "mdi:clipboard-play-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Execution Last Status",
            "wnhf_execution_last_status",
            "wnhf_execution_last_status",
        )

    @property
    def native_value(self) -> str:
        plan = self.engine.last_execution_plan
        return plan.status.value if plan is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        plan = self.engine.last_execution_plan
        if plan is not None:
            attrs.update(plan.as_dict())
        return attrs


class WNHFExecutionLastSteps(WNHFExecutionEntity, SensorEntity):
    """Expose number of steps in the latest dry-run plan."""

    _attr_icon = "mdi:format-list-numbered"
    _attr_native_unit_of_measurement = "steps"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Execution Last Steps",
            "wnhf_execution_last_steps",
            "wnhf_execution_last_steps",
        )

    @property
    def native_value(self) -> int:
        plan = self.engine.last_execution_plan
        return len(plan.steps) if plan is not None else 0

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        plan = self.engine.last_execution_plan
        if plan is not None:
            attrs.update(
                {
                    "decision_id": plan.decision_id,
                    "status": plan.status.value,
                    "active_step_count": sum(
                        1 for item in plan.steps
                        if item.valid and item.currently_active
                    ),
                    "summary": {
                        "total_objects": plan.total_object_count,
                        "active_objects": plan.active_object_count,
                        "planned_steps": len(plan.steps),
                        "skipped_objects": plan.skipped_object_count,
                        "invalid_objects": plan.invalid_object_count,
                    },
                    "optimization": {
                        "removed_steps": plan.skipped_object_count,
                        "ratio_percent": plan.optimization_ratio,
                        "optimizer_version": plan.optimizer_version,
                    },
                    "steps": [item.as_dict() for item in plan.steps],
                }
            )
        return attrs



class WNHFExecutionLastTransaction(WNHFExecutionEntity, SensorEntity):
    """Expose the latest active execution transaction."""

    _attr_icon = "mdi:transit-connection-variant"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Execution Last Transaction",
            "wnhf_execution_last_transaction",
            "wnhf_execution_last_transaction",
        )

    @property
    def native_value(self) -> str:
        transaction = self.engine.last_execution_transaction
        return transaction.status.value if transaction is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        transaction = self.engine.last_execution_transaction
        if transaction is not None:
            attrs.update(transaction.as_dict())
        return attrs


class WNHFExecutionAuditCount(WNHFExecutionEntity, SensorEntity):
    """Expose the number of in-memory audit records."""

    _attr_icon = "mdi:history"
    _attr_native_unit_of_measurement = "records"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Execution Audit Count",
            "wnhf_execution_audit_count",
            "wnhf_execution_audit_count",
        )

    @property
    def native_value(self) -> int:
        return len(self.engine.execution_audit)

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update(
            {
                "limit": EXECUTION_AUDIT_LIMIT,
                "latest": (
                    self.engine.last_execution_transaction.as_dict()
                    if self.engine.last_execution_transaction is not None
                    else None
                ),
            }
        )
        return attrs


class WNHFPublicExecutionLastStatus(WNHFExecutionEntity, SensorEntity):
    """Latest result from the canonical public execution entry."""

    _attr_icon = "mdi:api"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Canonical Execution Last Status",
            # Preserve the historical unique ID to reuse the existing entity.
            "wnhf_public_execution_last_status",
            "wnhf_canonical_execution_last_status",
        )

    @property
    def native_value(self) -> str:
        result = self.engine.last_canonical_execution
        return str(result.get("state")) if result is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        result = self.engine.last_canonical_execution
        attrs = {
            "module": "Canonical Execution",
            "version": VERSION,
            "entry": "wnhf.execution_execute",
        }
        if result is not None:
            attrs.update(result)
        return attrs



class WNHFMultiStepPlanLastStatus(WNHFExecutionEntity, SensorEntity):
    """Expose the latest Stage-2.1 multi-step blueprint."""

    _attr_icon = "mdi:format-list-numbered"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Multi Step Plan Last Status",
            "wnhf_multi_step_plan_last_status",
            "wnhf_multi_step_plan_last_status",
        )

    @property
    def native_value(self) -> str:
        blueprint = self.engine.last_multi_step_blueprint
        return blueprint.status if blueprint is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        blueprint = self.engine.last_multi_step_blueprint
        if blueprint is not None:
            attrs.update(blueprint.as_dict())
        return attrs



class WNHFMultiStepSimulationLastStatus(
    WNHFExecutionEntity,
    SensorEntity,
):
    """Expose the latest Stage-2.2 transaction simulation."""

    _attr_icon = "mdi:timeline-check-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Multi Step Simulation Last Status",
            "wnhf_multi_step_simulation_last_status",
            "wnhf_multi_step_simulation_last_status",
        )

    @property
    def native_value(self) -> str:
        simulation = self.engine.last_multi_step_simulation
        return simulation.status.value if simulation is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        simulation = self.engine.last_multi_step_simulation
        if simulation is not None:
            attrs.update(simulation.as_dict())
        return attrs


class WNHFGenericTransactionLastState(WNHFExecutionEntity, SensorEntity):
    _attr_icon="mdi:state-machine"
    def __init__(self,hass:HomeAssistant,engine:WNHFEngine)->None:
        super().__init__(hass,engine,"Red Queen Generic Transaction Last State","wnhf_generic_transaction_last_state","wnhf_generic_transaction_last_state")
    @property
    def native_value(self)->str:
        result=self.engine.last_generic_transaction
        return result.state.value if result is not None else "none"
    @property
    def extra_state_attributes(self)->dict:
        attrs=super().extra_state_attributes
        result=self.engine.last_generic_transaction
        if result is not None: attrs.update(result.as_dict())
        return attrs



class WNHFRealStepLastState(WNHFExecutionEntity, SensorEntity):
    """Expose the latest Stage-3.2 real-step state."""

    _attr_icon = "mdi:play-circle-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Real Step Last State",
            "wnhf_real_step_last_state",
            "wnhf_real_step_last_state",
        )

    @property
    def native_value(self) -> str:
        result = self.engine.last_real_step_result
        return result.state.value if result is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        result = self.engine.last_real_step_result
        if result is not None:
            attrs.update(result.as_dict())
        return attrs



class WNHFSequentialRoomLastState(WNHFExecutionEntity, SensorEntity):
    """Expose the latest Stage-3.3 sequential room state."""

    _attr_icon = "mdi:format-list-checks"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Sequential Room Last State",
            "wnhf_sequential_room_last_state",
            "wnhf_sequential_room_last_state",
        )

    @property
    def native_value(self) -> str:
        result = self.engine.last_sequential_room_result
        return result.state.value if result is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        result = self.engine.last_sequential_room_result
        if result is not None:
            attrs.update(result.as_dict())
        return attrs



class WNHFHouseExecutionLastState(WNHFExecutionEntity, SensorEntity):
    """Expose the latest Stage-3.4 house execution state."""

    _attr_icon = "mdi:home-lightbulb-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen House Execution Last State",
            "wnhf_house_execution_last_state",
            "wnhf_house_execution_last_state",
        )

    @property
    def native_value(self) -> str:
        result = self.engine.last_house_execution_result
        return result.state.value if result is not None else "none"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        result = self.engine.last_house_execution_result
        if result is not None:
            attrs.update(result.as_dict())
        return attrs



class WNHFTransactionLockState(WNHFExecutionEntity, SensorEntity):
    """Expose the central Transaction Lock Manager state."""

    _attr_icon = "mdi:lock-check-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Transaction Lock State",
            "wnhf_transaction_lock_state",
            "wnhf_transaction_lock_state",
        )

    @property
    def native_value(self) -> str:
        manager = self.engine.transaction_lock_manager
        return "locked" if manager._locks else "unlocked"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update({
            "active_lock_count": len(
                self.engine.transaction_lock_manager._locks
            ),
            "last_lock_decision": (
                self.engine.last_lock_decision.as_dict()
                if self.engine.last_lock_decision is not None
                else None
            ),
        })
        return attrs



class WNHFTransactionQueueState(WNHFExecutionEntity, SensorEntity):
    """Expose current scheduler queue length."""

    _attr_icon = "mdi:format-list-numbered"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Transaction Queue State",
            "wnhf_transaction_queue_state",
            "wnhf_transaction_queue_state",
        )

    @property
    def native_value(self) -> int:
        return len(self.engine.transaction_lock_manager._queue)

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        attrs.update({
            "queue_count": len(
                self.engine.transaction_lock_manager._queue
            ),
            "active_lock_count": len(
                self.engine.transaction_lock_manager._locks
            ),
            "last_lock_decision": (
                self.engine.last_lock_decision.as_dict()
                if self.engine.last_lock_decision is not None
                else None
            ),
        })
        return attrs



class WNHFSystemReadiness(WNHFExecutionEntity, SensorEntity):
    """Expose the latest aggregated runtime-readiness result."""

    _attr_icon = "mdi:check-decagram-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen System Readiness",
            # Keep the historical unique ID so existing entity-registry entries
            # migrate without creating a duplicate entity.
            "wnhf_system_alpha_readiness",
            "wnhf_system_readiness",
        )

    @property
    def native_value(self) -> str:
        result = self.engine.last_system_status
        if result is None:
            return "unknown"
        return "ready" if result.runtime_ready else "not_ready"

    @property
    def extra_state_attributes(self) -> dict:
        attrs = {"module": "Release Diagnostics", "version": VERSION}
        result = self.engine.last_system_status
        if result is not None:
            attrs.update(result.as_dict())
        return attrs



class WNHFReleaseScope(WNHFExecutionEntity, SensorEntity):
    """Expose the active framework release channel."""

    _attr_icon = "mdi:package-variant-closed-check"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Release Scope",
            "wnhf_release_scope",
            "wnhf_release_scope",
        )

    @property
    def native_value(self) -> str:
        return RELEASE_CHANNEL

    @property
    def extra_state_attributes(self) -> dict:
        attrs = {"module": "Release Diagnostics", "version": VERSION}
        result = (
            self.engine.last_release_scope
            or self.engine.release_scope_snapshot()
        )
        attrs.update(result)
        return attrs



class WNHFReleasePhase(WNHFExecutionEntity, SensorEntity):
    """Expose the current framework release-preparation phase."""

    _attr_icon = "mdi:rocket-launch-outline"

    def __init__(self, hass: HomeAssistant, engine: WNHFEngine) -> None:
        super().__init__(
            hass,
            engine,
            "Red Queen Release Phase",
            # Keep the historical unique ID so existing entity-registry entries
            # are reused while the user-facing entity is renamed.
            "wnhf_alpha_release_candidate",
            "wnhf_release_phase",
        )

    @property
    def native_value(self) -> str:
        return RELEASE_PHASE

    @property
    def extra_state_attributes(self) -> dict:
        attrs = {"module": "Release Diagnostics", "version": VERSION}
        result = (
            self.engine.last_release_info
            or self.engine.release_info_snapshot()
        )
        attrs.update(result)
        return attrs
