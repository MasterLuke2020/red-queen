"""WNHF light domain object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capability import ObjectCapability


@dataclass(frozen=True, slots=True)
class Light:
    """A platform-independent light object."""

    object_id: str
    name: str
    room_id: str
    enabled: bool
    control_mode: str
    command_entity_id: str | None
    state_entity_ids: tuple[str, ...]

    @property
    def controllable(self) -> bool:
        """Return whether this light can safely be controlled."""
        return (
            self.enabled
            and self.control_mode == "toggle"
            and self.command_entity_id is not None
            and bool(self.state_entity_ids)
        )


    @property
    def supported_capability_ids(self) -> tuple[str, ...]:
        capabilities: list[str] = []
        if self.state_entity_ids:
            capabilities.append("lighting.monitor_state")
        if self.controllable:
            capabilities.extend((
                "lighting.turn_on",
                "lighting.turn_off",
                "lighting.toggle",
            ))
        return tuple(capabilities)

    def object_capabilities(self) -> tuple[ObjectCapability, ...]:
        result: list[ObjectCapability] = []
        for capability_id in self.supported_capability_ids:
            monitor = capability_id == "lighting.monitor_state"
            result.append(ObjectCapability(
                object_id=self.object_id,
                object_type="light",
                room_id=self.room_id,
                capability_id=capability_id,
                supported=True,
                enabled=self.enabled,
                command_entity_ids=(
                    () if monitor or self.command_entity_id is None
                    else (self.command_entity_id,)
                ),
                feedback_entity_ids=tuple(self.state_entity_ids),
                reason=(
                    "Lighting feedback is configured."
                    if monitor
                    else "Guarded command and feedback are configured."
                ),
            ))
        return tuple(result)

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation for the Registry Explorer."""
        return {
            "id": self.object_id,
            "object_type": "light",
            "name": self.name,
            "room_id": self.room_id,
            "enabled": self.enabled,
            "control_mode": self.control_mode,
            "controllable": self.controllable,
            "command_entity_id": self.command_entity_id,
            "state_entity_ids": list(self.state_entity_ids),
            "capabilities": list(self.supported_capability_ids),
        }
