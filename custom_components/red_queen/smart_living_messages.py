"""Manual Smart Living message composer using canonical Red Queen routing."""
from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from time import monotonic
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SERVICE_EXECUTION_EXECUTE
from .smart_living_logic import permission

SIGNAL_COMPOSER_UPDATED = "wnhf_smart_living_composer_updated"
MESSAGE_PROFILES = ("mobile", "voice", "broadcast")
MESSAGE_PRIORITIES = ("info", "warning", "critical")


class SmartMessageComposer:
    """Nonpersistent manual text and canonical notification route dispatcher."""

    def __init__(self, hass: HomeAssistant, runtime) -> None:
        self.hass = hass
        self.runtime = runtime
        self.text = ""
        self.profile = "mobile"
        self.priority = "info"
        self.route_id = "notification.route.house"
        self._last_fingerprint: tuple[Any, ...] | None = None
        self._last_sent_at = 0.0
        self.audit: deque[dict[str, Any]] = deque(maxlen=50)

    def set_text(self, value: str) -> None:
        if not isinstance(value, str) or len(value) > 256:
            raise HomeAssistantError("Message must contain at most 256 characters")
        self.text = value
        async_dispatcher_send(self.hass, SIGNAL_COMPOSER_UPDATED)

    def set_profile(self, profile: str) -> None:
        if profile not in MESSAGE_PROFILES:
            raise HomeAssistantError("Unsupported message profile")
        self.profile = profile
        async_dispatcher_send(self.hass, SIGNAL_COMPOSER_UPDATED)

    def set_priority(self, priority: str) -> None:
        if priority not in MESSAGE_PRIORITIES:
            raise HomeAssistantError("Unsupported message priority")
        self.priority = priority
        async_dispatcher_send(self.hass, SIGNAL_COMPOSER_UPDATED)

    async def async_send(self) -> dict[str, Any]:
        message = self.text.strip()
        if not message:
            raise HomeAssistantError("Message is empty")
        if self.profile != "mobile":
            urgency = {"info": "info", "warning": "warning", "critical": "alarm"}[self.priority]
            allowed, reason = permission(
                self.runtime.mode, quiet=self.runtime.quiet,
                category="notifications.announce", urgency=urgency,
            )
            if not allowed:
                raise HomeAssistantError(reason)

        fingerprint = (message, self.profile, self.priority)
        if (fingerprint == self._last_fingerprint and
                monotonic() - self._last_sent_at < 10):
            raise HomeAssistantError("Identical message suppressed for 10 seconds")
        result = await self.hass.services.async_call(
            DOMAIN, SERVICE_EXECUTION_EXECUTE,
            {
                "action_id": "notifications.route",
                "target": {"object_id": self.route_id},
                "parameters": {
                    "message": message,
                    "title": "Red Queen",
                    "priority": self.priority,
                    "profile": self.profile,
                    "source": "smart_living",
                    "category": "manual",
                },
                "confirmed": False,
            },
            blocking=True,
            return_response=True,
        )
        payload = dict(result or {})
        accepted = payload.get("state") in {"succeeded", "no_action"}
        self.audit.append({
            "at": datetime.now(UTC).isoformat(),
            "route": self.route_id,
            "profile": self.profile,
            "priority": self.priority,
            "state": payload.get("state", "no_response"),
            "note": "Service dispatch only; delivery or audibility not proven",
        })
        if not accepted:
            raise HomeAssistantError(
                str(payload.get("reason") or payload.get("error") or
                    "Notification routing rejected")
            )
        self._last_fingerprint = fingerprint
        self._last_sent_at = monotonic()
        return payload
