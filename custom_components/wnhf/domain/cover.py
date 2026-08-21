"""WNHF cover domain object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capability import ObjectCapability


@dataclass(frozen=True, slots=True)
class Cover:
    """A platform-independent venetian-blind object."""

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
    closed_percent_feedback_entity_id: str | None
    capabilities: tuple[str, ...]

    @property
    def direction_feedback_entity_ids(self) -> tuple[str, ...]:
        """Return end-state and movement feedback used for safe execution."""
        return (
            self.open_feedback_entity_id,
            self.closed_feedback_entity_id,
            self.opening_feedback_entity_id,
            self.closing_feedback_entity_id,
        )

    @property
    def feedback_entity_ids(self) -> tuple[str, ...]:
        """Return all objective feedback entities, including position feedback."""
        entity_ids = list(self.direction_feedback_entity_ids)
        if self.closed_percent_feedback_entity_id:
            entity_ids.append(self.closed_percent_feedback_entity_id)
        return tuple(entity_ids)

    @property
    def supported_capability_ids(self) -> tuple[str, ...]:
        """Return configured semantic cover capabilities.

        Directional travel capabilities are effect-qualified through objective
        movement/end-state feedback. Blade commands are intentionally exposed
        with dispatch-scoped qualification because blade-position feedback is
        uncommon for venetian blinds.
        """
        result = ["covers.monitor_state"]
        if "open" in self.capabilities:
            result.append("covers.open")
        if "close" in self.capabilities:
            result.append("covers.close")
        if "blades_open" in self.capabilities:
            result.append("covers.blades_open")
        if "blades_close" in self.capabilities:
            result.append("covers.blades_close")
        return tuple(result)

    def object_capabilities(self) -> tuple[ObjectCapability, ...]:
        """Return object-level semantic cover capability declarations."""
        result: list[ObjectCapability] = []

        for capability_id in self.supported_capability_ids:
            commands: tuple[str, ...] = ()
            feedback = (
                self.feedback_entity_ids
                if capability_id == "covers.monitor_state"
                else self.direction_feedback_entity_ids
            )
            if capability_id == "covers.open":
                commands = (self.open_command_entity_id,)
            elif capability_id == "covers.close":
                commands = (self.close_command_entity_id,)
            elif capability_id == "covers.blades_open":
                commands = (self.blades_open_command_entity_id,)
                feedback = ()
            elif capability_id == "covers.blades_close":
                commands = (self.blades_close_command_entity_id,)
                feedback = ()

            result.append(ObjectCapability(
                object_id=self.object_id,
                object_type="cover",
                room_id=self.room_id,
                capability_id=capability_id,
                supported=True,
                enabled=self.enabled,
                command_entity_ids=commands,
                feedback_entity_ids=feedback,
                reason=(
                    "Objective cover movement/end-state feedback is configured."
                    if capability_id == "covers.monitor_state"
                    else (
                        "Configured blade command is available; execution is "
                        "qualified at dispatch scope without claiming a blade "
                        "position."
                        if capability_id in {
                            "covers.blades_open",
                            "covers.blades_close",
                        }
                        else "Directional cover command and feedback are configured."
                    )
                ),
            ))

        return tuple(result)

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
                "closed_percent_entity_id": self.closed_percent_feedback_entity_id,
            },
            "capabilities": list(self.capabilities),
            "semantic_capabilities": list(self.supported_capability_ids),
            "canonical_blade_execution_available": all(
                capability in self.capabilities
                for capability in ("blades_open", "blades_close")
            ),
        }
