"""Universal technical command dispatcher."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .capability import ExecutionCapability
from .real_step import CommandOutcome, CommandStatus


class CommandDispatcher:
    """Dispatch resolved commands without evaluating their effect."""

    VERSION = "1.0-stage4.3.2B.4B"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def async_dispatch(
        self,
        capability: ExecutionCapability,
    ) -> CommandOutcome:
        """Dispatch exactly one qualified Home Assistant service call."""
        if (
            not capability.command_domain
            or not capability.command_service
            or not capability.command_entity_id
        ):
            return CommandOutcome(
                status=CommandStatus.FAILED,
                attempted=False,
                dispatched=False,
                completed=False,
                domain=capability.command_domain,
                service=capability.command_service,
                entity_id=capability.command_entity_id,
                message="Resolved capability has no complete command.",
            )

        try:
            await self._hass.services.async_call(
                capability.command_domain,
                capability.command_service,
                {"entity_id": capability.command_entity_id},
                blocking=True,
            )
        except Exception as err:  # noqa: BLE001
            return CommandOutcome(
                status=CommandStatus.FAILED,
                attempted=True,
                dispatched=False,
                completed=False,
                domain=capability.command_domain,
                service=capability.command_service,
                entity_id=capability.command_entity_id,
                message=f"{type(err).__name__}: {err}",
            )

        return CommandOutcome(
            status=CommandStatus.SUCCEEDED,
            attempted=True,
            dispatched=True,
            completed=True,
            domain=capability.command_domain,
            service=capability.command_service,
            entity_id=capability.command_entity_id,
            message="Command dispatched successfully.",
        )
