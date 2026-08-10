"""Shared native entity support for WNHF."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.const import EntityCategory
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    VERSION,
    SIGNAL_PERFORMANCE_UPDATED,
    SIGNAL_REGISTRY_RELOADED,
    SIGNAL_VALIDATION_UPDATED,
    SIGNAL_HOUSE_UPDATED,
    SIGNAL_CAPABILITIES_UPDATED,
    SIGNAL_RULES_UPDATED,
    SIGNAL_CONTEXT_UPDATED,
    SIGNAL_POLICIES_UPDATED,
    SIGNAL_DECISIONS_UPDATED,
    SIGNAL_EXECUTIONS_UPDATED,
    SIGNAL_EXECUTION_AUDIT_UPDATED,
    SIGNAL_EXECUTION_EXECUTE_UPDATED,
)
from .device import framework_device_info, module_device_info
from .engine import WNHFEngine


class WNHFLightingEntity(Entity):
    """Base class for native WNHF lighting status entities."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_suggested_object_id = suggested_object_id
        self._attr_device_info = module_device_info(
            "lighting",
            "Red Queen Lighting",
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to feedback and registry changes."""
        await super().async_added_to_hass()

        @callback
        def async_feedback_changed(event: Event) -> None:
            self.async_write_ha_state()

        feedback_entities = self.engine.lighting_feedback_entities()
        if feedback_entities:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    feedback_entities,
                    async_feedback_changed,
                )
            )

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_REGISTRY_RELOADED,
                self._async_registry_reloaded,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_PERFORMANCE_UPDATED,
                self._async_registry_reloaded,
            )
        )

    @callback
    def _async_registry_reloaded(self) -> None:
        """Refresh state after a registry reload."""
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return common diagnostic attributes."""
        return {
            "module": "FB_Lighting",
            "version": VERSION,
        }


class WNHFDiagnosticEntity(Entity):
    """Base class for native WNHF diagnostic entities."""

    _attr_should_poll = False
    _attr_has_entity_name = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_suggested_object_id = suggested_object_id
        self._attr_device_info = framework_device_info()

    async def async_added_to_hass(self) -> None:
        """Refresh diagnostics after a registry reload."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_REGISTRY_RELOADED,
                self._async_registry_reloaded,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_PERFORMANCE_UPDATED,
                self._async_registry_reloaded,
            )
        )

    @callback
    def _async_registry_reloaded(self) -> None:
        """Write a new state after the registry changes."""
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return common framework metadata."""
        return {
            "module": "Diagnostics",
            "version": VERSION,
        }


class WNHFOpeningEntity(Entity):
    """Base class for native WNHF opening status entities."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_suggested_object_id = suggested_object_id
        self._attr_device_info = module_device_info(
            "openings",
            "Red Queen Openings",
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to all opening feedback changes."""
        await super().async_added_to_hass()

        @callback
        def async_feedback_changed(event: Event) -> None:
            self.async_write_ha_state()

        feedback_entities = self.engine.opening_feedback_entities()
        if feedback_entities:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    feedback_entities,
                    async_feedback_changed,
                )
            )

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_REGISTRY_RELOADED,
                self._async_registry_reloaded,
            )
        )

    @callback
    def _async_registry_reloaded(self) -> None:
        """Refresh state after a registry reload."""
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return common opening metadata."""
        return {
            "module": "Openings",
            "version": VERSION,
        }


class WNHFSecurityEntity(WNHFOpeningEntity):
    """Base class for native WNHF security entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        super().__init__(
            hass,
            engine,
            name,
            unique_id,
            suggested_object_id,
        )
        self._attr_device_info = module_device_info(
            "security",
            "Red Queen Security",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return common security metadata."""
        return {
            "module": "Security",
            "version": VERSION,
        }


class WNHFValidationEntity(WNHFDiagnosticEntity):
    """Base class for WNHF validator entities."""

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_VALIDATION_UPDATED,
                self._async_registry_reloaded,
            )
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "module": "Validator",
            "version": VERSION,
        }


class WNHFHouseEntity(Entity):
    """Base class for aggregate WNHF House Engine entities."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_suggested_object_id = suggested_object_id
        self._attr_device_info = module_device_info(
            "house",
            "Red Queen House Engine",
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to every source that affects the house aggregate."""
        await super().async_added_to_hass()

        @callback
        def async_feedback_changed(event: Event) -> None:
            self.async_write_ha_state()

        feedback_entities = self.engine.house_feedback_entities()
        if feedback_entities:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    feedback_entities,
                    async_feedback_changed,
                )
            )

        for signal in (
            SIGNAL_REGISTRY_RELOADED,
            SIGNAL_VALIDATION_UPDATED,
            SIGNAL_HOUSE_UPDATED,
        ):
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    signal,
                    self._async_house_updated,
                )
            )

    @callback
    def _async_house_updated(self) -> None:
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "module": "House Engine",
            "version": VERSION,
        }


class WNHFCapabilityEntity(Entity):
    """Base class for capability/provider diagnostic entities."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_suggested_object_id = suggested_object_id
        self._attr_device_info = module_device_info(
            "capabilities",
            "Red Queen Capabilities",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        for signal in (
            SIGNAL_REGISTRY_RELOADED,
            SIGNAL_VALIDATION_UPDATED,
            SIGNAL_CAPABILITIES_UPDATED,
        ):
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    signal,
                    self._async_capabilities_updated,
                )
            )

    @callback
    def _async_capabilities_updated(self) -> None:
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "module": "Capabilities",
            "version": VERSION,
        }


class WNHFRuleEntity(Entity):
    """Base class for generic Rule Engine diagnostics."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_suggested_object_id = suggested_object_id
        self._attr_device_info = module_device_info(
            "rules",
            "Red Queen Rule Engine",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        for signal in (
            SIGNAL_REGISTRY_RELOADED,
            SIGNAL_HOUSE_UPDATED,
            SIGNAL_CAPABILITIES_UPDATED,
            SIGNAL_RULES_UPDATED,
        ):
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    signal,
                    self._async_rules_updated,
                )
            )

    @callback
    def _async_rules_updated(self) -> None:
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "module": "Rule Engine",
            "version": VERSION,
            "rules_dir": str(self.engine.rules_dir),
        }


class WNHFContextEntity(Entity):
    """Base class for semantic Context Engine entities."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_suggested_object_id = suggested_object_id
        self._attr_device_info = module_device_info(
            "context",
            "Red Queen Context Engine",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def async_feedback_changed(event: Event) -> None:
            self.async_write_ha_state()

        feedback_entities = self.engine.house_feedback_entities()
        if feedback_entities:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    feedback_entities,
                    async_feedback_changed,
                )
            )

        for signal in (
            SIGNAL_REGISTRY_RELOADED,
            SIGNAL_VALIDATION_UPDATED,
            SIGNAL_HOUSE_UPDATED,
            SIGNAL_CAPABILITIES_UPDATED,
            SIGNAL_RULES_UPDATED,
            SIGNAL_CONTEXT_UPDATED,
        ):
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    signal,
                    self._async_context_updated,
                )
            )

    @callback
    def _async_context_updated(self) -> None:
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "module": "Context Engine",
            "version": VERSION,
        }


class WNHFPolicyEntity(Entity):
    """Base class for Policy Engine diagnostic entities."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_suggested_object_id = suggested_object_id
        self._attr_device_info = module_device_info(
            "policies",
            "Red Queen Policy Engine",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        for signal in (
            SIGNAL_CONTEXT_UPDATED,
            SIGNAL_RULES_UPDATED,
            SIGNAL_CAPABILITIES_UPDATED,
            SIGNAL_POLICIES_UPDATED,
            SIGNAL_REGISTRY_RELOADED,
        ):
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    signal,
                    self._async_policy_updated,
                )
            )

    @callback
    def _async_policy_updated(self) -> None:
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "module": "Policy Engine",
            "version": VERSION,
            "policies_dir": str(self.engine.policies_dir),
        }


class WNHFDecisionEntity(Entity):
    """Base class for read-only Decision Engine entities."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_suggested_object_id = suggested_object_id
        self._attr_device_info = module_device_info(
            "decisions",
            "Red Queen Decision Engine",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        for signal in (
            SIGNAL_CONTEXT_UPDATED,
            SIGNAL_POLICIES_UPDATED,
            SIGNAL_DECISIONS_UPDATED,
            SIGNAL_RULES_UPDATED,
            SIGNAL_CAPABILITIES_UPDATED,
            SIGNAL_REGISTRY_RELOADED,
        ):
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    signal,
                    self._async_decision_updated,
                )
            )

    @callback
    def _async_decision_updated(self) -> None:
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "module": "Decision Engine",
            "version": VERSION,
            "read_only": True,
            "decisions_dir": str(self.engine.decisions_dir),
        }


class WNHFExecutionEntity(Entity):
    """Base class for dry-run Execution Engine entities."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(
        self,
        hass: HomeAssistant,
        engine: WNHFEngine,
        name: str,
        unique_id: str,
        suggested_object_id: str,
    ) -> None:
        self.hass = hass
        self.engine = engine
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_suggested_object_id = suggested_object_id
        self._attr_device_info = module_device_info(
            "executions",
            "Red Queen Execution Engine",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        for signal in (
            SIGNAL_CONTEXT_UPDATED,
            SIGNAL_POLICIES_UPDATED,
            SIGNAL_DECISIONS_UPDATED,
            SIGNAL_EXECUTIONS_UPDATED,
            SIGNAL_EXECUTION_EXECUTE_UPDATED,
            SIGNAL_REGISTRY_RELOADED,
        ):
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass,
                    signal,
                    self._async_execution_updated,
                )
            )

    @callback
    def _async_execution_updated(self) -> None:
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "module": "Execution Engine",
            "version": VERSION,
            "dry_run": True,
            "executed": False,
        }
