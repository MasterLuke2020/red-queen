"""WNHF cover domain object."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class Cover:
    object_id: str
    name: str
    room_id: str
    cover_type: str
    enabled: bool
    open_command_entity_id: str
    close_command_entity_id: str
    blades_open_command_entity_id: str
    blades_close_command_entity_id: str
    open_feedback_entity_id: str
    closed_feedback_entity_id: str
    opening_feedback_entity_id: str
    closing_feedback_entity_id: str
    capabilities: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.object_id,
            "object_type": "cover",
            "name": self.name,
            "room_id": self.room_id,
            "cover_type": self.cover_type,
            "enabled": self.enabled,
            "commands": {
                "open_entity_id": self.open_command_entity_id,
                "close_entity_id": self.close_command_entity_id,
                "blades_open_entity_id": self.blades_open_command_entity_id,
                "blades_close_entity_id": self.blades_close_command_entity_id,
            },
            "feedback": {
                "open_entity_id": self.open_feedback_entity_id,
                "closed_entity_id": self.closed_feedback_entity_id,
                "opening_entity_id": self.opening_feedback_entity_id,
                "closing_entity_id": self.closing_feedback_entity_id,
            },
            "capabilities": list(self.capabilities),
        }
