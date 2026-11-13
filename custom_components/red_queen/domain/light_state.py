"""Runtime state model for WNHF lights."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .light import Light


@dataclass(frozen=True, slots=True)
class LightSnapshot:
    """Immutable runtime snapshot of one WNHF light."""

    light: Light
    is_on: bool
    available: bool
    feedback_states: dict[str, str | None]

    @property
    def is_off(self) -> bool:
        """Return whether the light is available and currently off."""
        return self.available and not self.is_on

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "id": self.light.object_id,
            "name": self.light.name,
            "room_id": self.light.room_id,
            "is_on": self.is_on,
            "is_off": self.is_off,
            "available": self.available,
            "control_mode": self.light.control_mode,
            "controllable": self.light.controllable,
            "command_entity_id": self.light.command_entity_id,
            "feedback_states": self.feedback_states,
        }
