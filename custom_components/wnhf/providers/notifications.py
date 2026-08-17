
"""Core provider for semantic notification dispatch."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..const import NOTIFICATION_TARGETS_FILE
from ..domain.capability import CapabilitySnapshot, CapabilityState
from ..domain.notification import NotificationTarget, load_notification_targets
from .base import ProviderKind, WNHFProvider
from .execution import ProviderExecutionResult, ProviderExecutionValidationResult


class NotificationCapabilityProvider(WNHFProvider):
    """Provider-neutral notification adapter for Home Assistant notify entities."""

    provider_name = "NotificationCapabilityProvider"
    provider_kind = ProviderKind.CORE
    provider_version = "1.0.0"
    discoverable = True
    priority = 100
    _ACTION_SEND = "notifications.send"

    def __init__(self, engine) -> None:
        super().__init__(engine.hass)
        self.engine = engine
        self._targets: dict[str, NotificationTarget] = {}
        self._load_error: str | None = None
        self._last_reload_at: str | None = None
        self._last_dispatch_at: dict[str, str] = {}

    @property
    def provider_id(self) -> str:
        return "provider.core.notifications"

    @property
    def _registry_path(self):
        return self.engine.registry_dir / NOTIFICATION_TARGETS_FILE

    def supported_capabilities(self) -> tuple[str, ...]:
        return ("notifications",)

    async def async_setup(self) -> None:
        await super().async_setup()
        await self._async_reload_targets()

    async def _async_reload_targets(self) -> None:
        try:
            targets = await self.hass.async_add_executor_job(
                load_notification_targets, self._registry_path
            )
        except Exception as err:  # noqa: BLE001
            self._targets = {}
            self._load_error = f"{type(err).__name__}: {err}"
        else:
            self._targets = targets
            self._load_error = None
        self._last_reload_at = datetime.now(UTC).isoformat()

    def _service_available(self) -> bool:
        return self.hass.services.has_service("notify", "send_message")

    def _target_available(self, target: NotificationTarget) -> bool:
        if not target.enabled or not self._service_available():
            return False
        state = self.hass.states.get(target.entity_id)
        return state is not None and state.state != "unavailable"

    def _technical(self, target: NotificationTarget) -> dict[str, Any]:
        return {
            "capability_id": "notifications",
            "action_id": self._ACTION_SEND,
            "target_id": target.object_id,
            "provider": target.provider,
            "entity_id": target.entity_id,
            "service": "notify.send_message",
            "available": self._target_available(target),
            "verification_scope": "dispatch",
            "delivery_receipt_claimed": False,
            "read_receipt_claimed": False,
        }

    def snapshot(self) -> CapabilitySnapshot:
        configured = len(self._targets)
        enabled = [t for t in self._targets.values() if t.enabled]
        available_targets = [t for t in enabled if self._target_available(t)]
        supported = configured > 0
        available = (
            supported
            and self._load_error is None
            and self._service_available()
            and bool(available_targets)
        )
        healthy = available

        if not supported:
            state = CapabilityState.UNSUPPORTED
            message = (
                "Notifications are not configured."
                if self._load_error is None
                else "Notification target registry is invalid."
            )
        elif not available:
            state = CapabilityState.UNAVAILABLE
            message = (
                "Notification targets are configured but no enabled target "
                "is currently dispatchable."
            )
        else:
            state = CapabilityState.HEALTHY
            message = "Notifications available."

        targets = [
            {
                **t.as_dict(),
                "available": self._target_available(t),
                "last_dispatch_at": self._last_dispatch_at.get(t.object_id),
            }
            for t in sorted(self._targets.values(), key=lambda item: item.object_id)
        ]
        return CapabilitySnapshot(
            capability_id="notifications",
            provider_id=self.provider_id if supported else None,
            supported=supported,
            available=available,
            healthy=healthy,
            state=state,
            message=message,
            details={
                "registry_file": str(self._registry_path),
                "configured_targets": configured,
                "enabled_targets": len(enabled),
                "available_targets": len(available_targets),
                "notify_send_message_available": self._service_available(),
                "load_error": self._load_error,
                "last_reload_at": self._last_reload_at,
                "targets": targets,
                "canonical_actions": [self._ACTION_SEND],
                "verification_scope": "dispatch",
                "delivery_receipt_claimed": False,
                "read_receipt_claimed": False,
            },
        )

    async def async_validate_execution(
        self, *, action_id: str, target: dict[str, Any],
        parameters: dict[str, Any], confirmed: bool,
    ) -> ProviderExecutionValidationResult:
        if action_id != self._ACTION_SEND:
            return await super().async_validate_execution(
                action_id=action_id, target=target, parameters=parameters,
                confirmed=confirmed,
            )

        await self._async_reload_targets()
        object_id = target.get("object_id")
        if not isinstance(object_id, str) or not object_id.strip():
            return ProviderExecutionValidationResult(
                valid=False,
                reason="notifications.send requires target.object_id.",
                errors=("target.object_id is required.",),
            )

        message = parameters.get("message")
        title = parameters.get("title")
        if not isinstance(message, str) or not message.strip():
            return ProviderExecutionValidationResult(
                valid=False,
                reason="notifications.send requires a non-empty message.",
                errors=("parameters.message must be a non-empty string.",),
            )
        if title is not None and not isinstance(title, str):
            return ProviderExecutionValidationResult(
                valid=False,
                reason="notifications.send title must be a string or null.",
                errors=("parameters.title must be a string or null.",),
            )

        semantic_target = self._targets.get(object_id)
        if semantic_target is None:
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Unknown semantic notification target: {object_id}.",
                errors=(f"Unknown semantic notification target: {object_id}.",),
            )
        technical = self._technical(semantic_target)
        if not semantic_target.enabled:
            return ProviderExecutionValidationResult(
                valid=False, reason=f"Notification target {object_id} is disabled.",
                errors=(f"Notification target {object_id} is disabled.",),
                technical_capability=technical,
            )
        if not self._service_available():
            return ProviderExecutionValidationResult(
                valid=False,
                reason="Home Assistant notify.send_message is unavailable.",
                errors=("notify.send_message service is unavailable.",),
                technical_capability=technical,
            )
        if not self._target_available(semantic_target):
            return ProviderExecutionValidationResult(
                valid=False,
                reason=f"Notification target {object_id} is currently unavailable.",
                errors=(f"{semantic_target.entity_id} is unavailable.",),
                technical_capability=technical,
            )
        return ProviderExecutionValidationResult(
            valid=True,
            reason=(
                "Notification target, portable message parameters and Home "
                "Assistant notify entity are valid for canonical dispatch."
            ),
            technical_capability=technical,
        )

    async def async_execute(
        self, *, action_id: str, target: dict[str, Any],
        parameters: dict[str, Any], confirmed: bool,
    ) -> ProviderExecutionResult:
        if action_id != self._ACTION_SEND:
            return await super().async_execute(
                action_id=action_id, target=target, parameters=parameters,
                confirmed=confirmed,
            )

        validation = await self.async_validate_execution(
            action_id=action_id, target=target, parameters=parameters,
            confirmed=confirmed,
        )
        if not validation.valid:
            return ProviderExecutionResult(
                status="rejected", executed=False, command_sent=False,
                feedback_confirmed=False, reason=validation.reason,
                technical_capability=validation.technical_capability,
                verification_scope="dispatch",
            )

        object_id = str(target["object_id"])
        semantic_target = self._targets[object_id]
        service_data: dict[str, Any] = {
            "entity_id": semantic_target.entity_id,
            "message": str(parameters["message"]),
        }
        title = parameters.get("title")
        if isinstance(title, str):
            service_data["title"] = title

        try:
            await self.hass.services.async_call(
                "notify", "send_message", service_data, blocking=True
            )
        except Exception as err:  # noqa: BLE001
            return ProviderExecutionResult(
                status="failed", executed=False, command_sent=False,
                feedback_confirmed=False,
                reason="Home Assistant notification dispatch failed.",
                error=f"{type(err).__name__}: {err}",
                technical_capability=validation.technical_capability,
                verification_scope="dispatch",
            )

        dispatched_at = datetime.now(UTC).isoformat()
        self._last_dispatch_at[object_id] = dispatched_at
        return ProviderExecutionResult(
            status="succeeded", executed=True, command_sent=True,
            # For dispatch-scoped execution this flag confirms completion of
            # the HA provider call, not remote delivery/read.
            feedback_confirmed=True,
            reason=(
                "Notification dispatch was accepted by the Home Assistant "
                "notify entity. Delivery/read receipt is not claimed."
            ),
            technical_capability=validation.technical_capability,
            feedback_after={
                "target_id": object_id,
                "entity_id": semantic_target.entity_id,
                "dispatched_at": dispatched_at,
                "verification_scope": "dispatch",
                "delivery_receipt_claimed": False,
                "read_receipt_claimed": False,
            },
            verification_scope="dispatch",
        )
