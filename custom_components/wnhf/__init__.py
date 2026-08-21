"""Red Queen integration (technical domain: wnhf)."""

from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later

from .const import (
    DATA_ENGINE,
    DOMAIN,
    EVENT_REGISTRY_LOADED,
    PLATFORMS,
    REGISTRY_ROOT,
    VERSION,
    SIGNAL_VALIDATION_UPDATED,
    SIGNAL_PERFORMANCE_UPDATED,
    SIGNAL_HOUSE_UPDATED,
    SIGNAL_CAPABILITIES_UPDATED,
    SIGNAL_RULES_UPDATED,
    SIGNAL_CONTEXT_UPDATED,
    SIGNAL_POLICIES_UPDATED,
    SIGNAL_DECISIONS_UPDATED,
    SIGNAL_EXECUTIONS_UPDATED,
    SIGNAL_EXECUTION_AUDIT_UPDATED,
)
from .engine import WNHFEngine
from .domain.house import House
from .registry import WNHFRegistryError
from .services import async_register_services, async_unregister_services

_LOGGER = logging.getLogger(__name__)

_DATA_STARTUP_VALIDATION_CANCEL = "startup_validation_cancel"

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({})},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Import the legacy YAML configuration into a config entry."""
    if DOMAIN not in config:
        return True

    if not hass.config_entries.async_entries(DOMAIN):
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data={},
            ),
            "Red Queen import configuration",
        )

    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Red Queen from its config entry."""
    registry_dir = Path(hass.config.path(*REGISTRY_ROOT))
    engine = WNHFEngine(hass, registry_dir)

    await engine.async_prepare_runtime()
    await engine.provider_discovery.async_discover()

    try:
        house = await engine.async_load_registry()
    except WNHFRegistryError as err:
        engine.safe_mode = True
        engine.startup_error = str(err)
        engine.house = House(
            object_id="recovery",
            name="Red Queen Recovery Mode",
            rooms={},
            lights={},
            openings={},
            covers={},
            plants={},
        )
        await engine.async_load_rules()
        await engine.async_load_policies()
        await engine.async_load_decisions()
        house = engine.house
        _LOGGER.error(
            "Red Queen registry damaged; starting in recovery mode: %s",
            err,
        )


    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][DATA_ENGINE] = engine
    hass.data[DOMAIN]["config_entry_id"] = entry.entry_id

    await async_register_services(hass, engine)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info(
        "Red Queen %s started via config entry | Rooms: %s | Lights: %s | "
        "Covers: %s | Openings: %s | Plants: %s | Warnings: %s | Registry: %.2f ms",
        VERSION,
        len(house.rooms),
        len(house.lights),
        len(house.covers),
        len(house.openings),
        len(house.plants),
        len(engine.registry_warnings),
        engine.registry_load_ms or 0.0,
    )

    for warning in engine.registry_warnings:
        _LOGGER.warning("Red Queen registry: %s", warning)

    async def async_run_startup_validation(_now) -> None:
        domain_data = hass.data.get(DOMAIN)
        if domain_data is None or domain_data.get(DATA_ENGINE) is not engine:
            return

        # The delayed callback is no longer pending once Home Assistant starts
        # executing it.  Clearing the cancel handle also makes unload
        # diagnostics accurately distinguish a pending callback from one that
        # already ran.
        domain_data.pop(_DATA_STARTUP_VALIDATION_CANCEL, None)

        report = await engine.async_validate_registry()

        # Validation may await executor work.  Do not dispatch stale updates if
        # the config entry was unloaded while validation was in progress.
        domain_data = hass.data.get(DOMAIN)
        if domain_data is None or domain_data.get(DATA_ENGINE) is not engine:
            return

        async_dispatcher_send(hass, SIGNAL_VALIDATION_UPDATED)
        async_dispatcher_send(hass, SIGNAL_PERFORMANCE_UPDATED)
        async_dispatcher_send(hass, SIGNAL_HOUSE_UPDATED)
        async_dispatcher_send(hass, SIGNAL_CAPABILITIES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_RULES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_CONTEXT_UPDATED)
        async_dispatcher_send(hass, SIGNAL_POLICIES_UPDATED)
        async_dispatcher_send(hass, SIGNAL_DECISIONS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_EXECUTIONS_UPDATED)
        async_dispatcher_send(hass, SIGNAL_EXECUTION_AUDIT_UPDATED)
        _LOGGER.info(
            "Red Queen startup validation: %s | errors=%s | warnings=%s | "
            "quality=%s%% | %.2f ms",
            report.status,
            len(report.errors),
            len(report.warnings),
            report.quality_score,
            report.duration_ms,
        )

    if not engine.safe_mode:
        hass.data[DOMAIN][_DATA_STARTUP_VALIDATION_CANCEL] = async_call_later(
            hass,
            5,
            async_run_startup_validation,
        )

    hass.bus.async_fire(
        EVENT_REGISTRY_LOADED,
        {
            "version": VERSION,
            "house_id": house.object_id,
            "house_name": house.name,
            "rooms": len(house.rooms),
            "lights": len(house.lights),
            "covers": len(house.covers),
            "openings": len(house.openings),
            "plants": len(house.plants),
            "warnings": list(engine.registry_warnings),
        },
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload the WNHF config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        domain_data = hass.data.get(DOMAIN, {})
        engine = domain_data.get(DATA_ENGINE)

        cancel_startup_validation = domain_data.pop(
            _DATA_STARTUP_VALIDATION_CANCEL,
            None,
        )
        startup_validation_cancelled = cancel_startup_validation is not None
        if cancel_startup_validation is not None:
            cancel_startup_validation()

        removed_services = async_unregister_services(hass)

        if engine is not None:
            await engine.provider_discovery.async_unload()

        hass.data.pop(DOMAIN, None)
        _LOGGER.info(
            "Red Queen config entry unloaded | services_removed=%s | "
            "startup_validation_cancelled=%s",
            len(removed_services),
            startup_validation_cancelled,
        )

    return unload_ok
