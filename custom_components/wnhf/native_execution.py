"""Canonical execution bridge for native Home Assistant entities."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, SERVICE_EXECUTION_EXECUTE


async def async_execute_canonical(
    hass: HomeAssistant,
    *,
    action_id: str,
    object_id: str,
    confirmed: bool = False,
) -> dict[str, Any]:
    """Execute one semantic action and surface canonical rejection to HA."""
    result = await hass.services.async_call(
        DOMAIN,
        SERVICE_EXECUTION_EXECUTE,
        {
            "action_id": action_id,
            "target": {"object_id": object_id},
            "parameters": {},
            "confirmed": confirmed,
        },
        blocking=True,
        return_response=True,
    )

    payload = dict(result or {})
    if payload.get("state") != "succeeded":
        reason = str(
            payload.get("reason")
            or payload.get("error")
            or f"Canonical action {action_id} was rejected."
        )
        raise HomeAssistantError(reason)

    return payload
