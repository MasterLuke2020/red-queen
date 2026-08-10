"""WNHF access and opening domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .capability import ObjectCapability


@dataclass(frozen=True, slots=True)
class DoorLock:
    """Optional lock configuration attached to a door opening."""

    feedback_entity_id: str
    locked_states: tuple[str, ...]
    lock_command_entity_id: str | None = None
    unlock_command_entity_id: str | None = None

    def state_is_locked(self, state: str | None) -> bool:
        """Return whether a platform state represents a locked condition."""
        return state in self.locked_states

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        capabilities = ["monitor_lock_state"]

        if self.lock_command_entity_id:
            capabilities.append("lock")

        if self.unlock_command_entity_id:
            capabilities.append("unlock")

        return {
            "feedback_entity_id": self.feedback_entity_id,
            "locked_states": list(self.locked_states),
            "lock_command_entity_id": self.lock_command_entity_id,
            "unlock_command_entity_id": self.unlock_command_entity_id,
            "capabilities": capabilities,
        }


@dataclass(frozen=True, slots=True)
class DoorOpener:
    """Optional electric door-opener configuration."""

    command_entity_id: str

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "command_entity_id": self.command_entity_id,
            "capabilities": ["door_open"],
        }


@dataclass(frozen=True, slots=True)
class GarageDoor:
    """Optional garage-door command and feedback configuration."""

    open_feedback_entity_id: str
    closed_feedback_entity_id: str
    toggle_command_entity_id: str
    movement_timeout_seconds: float
    stop_command_entity_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        capabilities = [
            "monitor_open_state",
            "monitor_closed_state",
            "toggle",
        ]

        if self.stop_command_entity_id:
            capabilities.append("stop")

        return {
            "open_feedback_entity_id": self.open_feedback_entity_id,
            "closed_feedback_entity_id": self.closed_feedback_entity_id,
            "toggle_command_entity_id": self.toggle_command_entity_id,
            "stop_command_entity_id": self.stop_command_entity_id,
            "movement_timeout_seconds": self.movement_timeout_seconds,
            "capabilities": capabilities,
        }


@dataclass(frozen=True, slots=True)
class Opening:
    """A platform-independent building access opening.

    Supported opening types:

    - ``window``
    - ``sliding_door``
    - ``door``
    - ``garage_door``

    ``state_entity_id`` and ``open_states`` remain the common feedback model
    for windows, sliding doors, and ordinary doors.

    Doors may additionally provide a lock and/or electric door opener.
    Garage doors may provide their dedicated two-sensor feedback and
    pulse-command configuration through ``garage_door``.
    """

    object_id: str
    name: str
    room_id: str
    opening_type: str
    enabled: bool
    state_entity_id: str | None
    open_states: tuple[str, ...]
    lock: DoorLock | None = None
    door_opener: DoorOpener | None = None
    garage_door: GarageDoor | None = None

    def state_is_open(self, state: str | None) -> bool:
        """Return whether a platform state represents an open condition."""
        return state in self.open_states

    @property
    def has_lock(self) -> bool:
        """Return whether the opening has a configured lock."""
        return self.lock is not None

    @property
    def has_door_opener(self) -> bool:
        """Return whether the opening has an electric door opener."""
        return self.door_opener is not None

    @property
    def is_garage_door(self) -> bool:
        """Return whether this object represents a garage door."""
        return self.opening_type == "garage_door"

    @property
    def supported_capability_ids(self) -> tuple[str, ...]:
        capabilities: list[str] = []
        if self.state_entity_id:
            capabilities.append("access.monitor_open_state")
        if self.lock is not None:
            capabilities.append("access.monitor_lock_state")
            if self.lock.lock_command_entity_id:
                capabilities.append("access.lock")
            if self.lock.unlock_command_entity_id:
                capabilities.append("access.unlock")
        if self.door_opener is not None:
            capabilities.append("access.door_open")
        if self.garage_door is not None:
            capabilities.extend((
                "access.monitor_garage_state",
                "access.toggle",
            ))
            if self.garage_door.stop_command_entity_id:
                capabilities.append("access.stop")
        return tuple(dict.fromkeys(capabilities))

    def object_capabilities(self) -> tuple[ObjectCapability, ...]:
        result: list[ObjectCapability] = []
        for capability_id in self.supported_capability_ids:
            commands: tuple[str, ...] = ()
            feedback: tuple[str, ...] = ()
            reason = "Configured Access capability."

            if capability_id == "access.monitor_open_state":
                feedback = (
                    (self.state_entity_id,)
                    if self.state_entity_id is not None else ()
                )
            elif capability_id == "access.monitor_lock_state" and self.lock:
                feedback = (self.lock.feedback_entity_id,)
            elif capability_id == "access.lock" and self.lock:
                commands = (
                    (self.lock.lock_command_entity_id,)
                    if self.lock.lock_command_entity_id else ()
                )
                feedback = (self.lock.feedback_entity_id,)
            elif capability_id == "access.unlock" and self.lock:
                commands = (
                    (self.lock.unlock_command_entity_id,)
                    if self.lock.unlock_command_entity_id else ()
                )
                feedback = (self.lock.feedback_entity_id,)
            elif capability_id == "access.door_open" and self.door_opener:
                commands = (self.door_opener.command_entity_id,)
            elif self.garage_door is not None:
                feedback = (
                    self.garage_door.open_feedback_entity_id,
                    self.garage_door.closed_feedback_entity_id,
                )
                if capability_id == "access.toggle":
                    commands = (
                        self.garage_door.toggle_command_entity_id,
                    )
                elif (
                    capability_id == "access.stop"
                    and self.garage_door.stop_command_entity_id
                ):
                    commands = (
                        self.garage_door.stop_command_entity_id,
                    )

            result.append(ObjectCapability(
                object_id=self.object_id,
                object_type="opening",
                room_id=self.room_id,
                capability_id=capability_id,
                supported=True,
                enabled=self.enabled,
                command_entity_ids=commands,
                feedback_entity_ids=feedback,
                reason=reason,
            ))
        return tuple(result)

    def capabilities(self) -> tuple[str, ...]:
        return self.supported_capability_ids

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "id": self.object_id,
            "object_type": "opening",
            "name": self.name,
            "room_id": self.room_id,
            "opening_type": self.opening_type,
            "enabled": self.enabled,
            "state_entity_id": self.state_entity_id,
            "open_states": list(self.open_states),
            "lock": self.lock.as_dict() if self.lock is not None else None,
            "door_opener": (
                self.door_opener.as_dict()
                if self.door_opener is not None
                else None
            ),
            "garage_door": (
                self.garage_door.as_dict()
                if self.garage_door is not None
                else None
            ),
            "capabilities": list(self.capabilities()),
        }
