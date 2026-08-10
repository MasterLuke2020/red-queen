"""Normalized runtime state for the WNHF Access domain."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class OpeningRuntimeState(StrEnum):
    """Normalized passive opening states."""

    OPEN = "open"
    CLOSED = "closed"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class LockRuntimeState(StrEnum):
    """Normalized optional door-lock states."""

    LOCKED = "locked"
    UNLOCKED = "unlocked"
    UNAVAILABLE = "unavailable"
    NOT_CONFIGURED = "not_configured"


class GarageDoorRuntimeState(StrEnum):
    """Normalized garage-door states derived from two end sensors."""

    OPEN = "open"
    CLOSED = "closed"
    MOVING = "moving"
    INTERMEDIATE_OPEN = "intermediate_open"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class AccessObjectSnapshot:
    """Immutable runtime snapshot of one Access object."""

    object_id: str
    name: str
    room_id: str
    opening_type: str
    enabled: bool
    available: bool
    state: str
    is_open: bool
    is_closed: bool
    secure: bool
    lock_state: str | None = None
    has_lock: bool = False
    has_door_opener: bool = False
    garage_elapsed_seconds: float | None = None
    feedback_states: dict[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "id": self.object_id,
            "name": self.name,
            "room_id": self.room_id,
            "opening_type": self.opening_type,
            "enabled": self.enabled,
            "available": self.available,
            "state": self.state,
            "is_open": self.is_open,
            "is_closed": self.is_closed,
            "secure": self.secure,
            "lock_state": self.lock_state,
            "has_lock": self.has_lock,
            "has_door_opener": self.has_door_opener,
            "garage_elapsed_seconds": self.garage_elapsed_seconds,
            "feedback_states": dict(self.feedback_states or {}),
        }


@dataclass(frozen=True, slots=True)
class AccessSnapshot:
    """Immutable aggregate snapshot of the complete Access domain."""

    generated_at: str
    total: int
    enabled: int
    available: int
    secure: int
    open_count: int
    unavailable_count: int
    windows: int
    sliding_doors: int
    doors: int
    garage_doors: int
    locked_doors: int
    unlocked_doors: int
    garage_open: int
    garage_closed: int
    garage_moving: int
    garage_intermediate_open: int
    garage_error: int
    objects: tuple[AccessObjectSnapshot, ...]

    @property
    def all_available(self) -> bool:
        """Return whether every enabled Access object is available."""
        return self.enabled == self.available

    @property
    def all_secure(self) -> bool:
        """Return whether every enabled Access object is currently secure."""
        return self.enabled > 0 and self.enabled == self.secure

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "api_version": "1.0",
            "generated_at": self.generated_at,
            "summary": {
                "total": self.total,
                "enabled": self.enabled,
                "available": self.available,
                "unavailable": self.unavailable_count,
                "secure": self.secure,
                "open": self.open_count,
                "all_available": self.all_available,
                "all_secure": self.all_secure,
            },
            "types": {
                "windows": self.windows,
                "sliding_doors": self.sliding_doors,
                "doors": self.doors,
                "garage_doors": self.garage_doors,
            },
            "doors": {
                "locked": self.locked_doors,
                "unlocked": self.unlocked_doors,
            },
            "garage": {
                "open": self.garage_open,
                "closed": self.garage_closed,
                "moving": self.garage_moving,
                "intermediate_open": self.garage_intermediate_open,
                "error": self.garage_error,
            },
            "objects": [item.as_dict() for item in self.objects],
        }
