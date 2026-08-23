"""Canonical execution bridge for native Home Assistant entities."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, SERVICE_EXECUTION_EXECUTE

_LOGGER = logging.getLogger(__name__)


def _rejection_translation(action_id: str, reason: str) -> tuple[str, dict[str, str]]:
    """Map common canonical guards to concise user-facing translations."""
    text = reason.lower()

    if action_id in {"openings.lock", "openings.unlock"} and (
        "door is open" in text or "closed door" in text
    ):
        return "door_open_lock_blocked", {}

    if action_id == "openings.release" and (
        "door is open" in text
        or "closed door" in text
        or "door contact" in text
    ):
        return "door_open_release_blocked", {}

    if action_id in {"covers.blades_open", "covers.blades_close"} and "moving" in text:
        return "cover_blades_moving", {}

    if action_id in {"covers.open", "covers.close"} and (
        "opposite direction" in text or "reversal" in text
    ):
        return "cover_reversal_blocked", {}

    if action_id == "garage.stop" and (
        "only while" in text or "moving" in text
    ):
        return "garage_stop_not_moving", {}

    if action_id in {"garage.open", "garage.close"}:
        if "already moving" in text:
            return "garage_moving_blocked", {}
        if "intermediate" in text or "ambiguous" in text:
            return "garage_intermediate_blocked", {}
        if "contradictory" in text:
            return "garage_feedback_conflict", {}
        if "unavailable" in text:
            return "garage_feedback_unavailable", {}
        if "proven open or closed" in text or "end position" in text:
            return "garage_end_state_required", {}

    if "unavailable" in text:
        return "command_unavailable", {}

    return "canonical_action_rejected", {"action_id": action_id}


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

    # Canonical execution intentionally uses no_action for an already satisfied
    # request and in_progress when the requested movement is already underway.
    # Both are successful/idempotent outcomes from a native HA control and must
    # not be surfaced as user-facing errors.
    if payload.get("state") not in {"succeeded", "no_action", "in_progress"}:
        reason = str(
            payload.get("reason")
            or payload.get("error")
            or f"Canonical action {action_id} was rejected."
        )
        _LOGGER.warning(
            "Canonical action rejected: action_id=%s object_id=%s code=%s reason=%s",
            action_id,
            object_id,
            payload.get("code"),
            reason,
        )
        translation_key, placeholders = _rejection_translation(action_id, reason)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key=translation_key,
            translation_placeholders=placeholders,
        )

    return payload
