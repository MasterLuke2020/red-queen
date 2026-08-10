"""Platform-independent WNHF security domain model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .access_state import AccessObjectSnapshot, AccessSnapshot


@dataclass(frozen=True, slots=True)
class SecuritySnapshot:
    """Semantic house security state derived from the Access domain."""

    secure: bool
    all_access_available: bool
    access_attention_required: bool
    alert: bool
    level: str
    open_count: int
    insecure_count: int
    unavailable_count: int
    attention_count: int
    open_objects: tuple[AccessObjectSnapshot, ...]
    insecure_objects: tuple[AccessObjectSnapshot, ...]
    unavailable_objects: tuple[AccessObjectSnapshot, ...]
    attention_objects: tuple[AccessObjectSnapshot, ...]

    @property
    def opening_ids(self) -> tuple[str, ...]:
        """Retain the previous public list of open object IDs."""
        return tuple(item.object_id for item in self.open_objects)

    @property
    def opening_names(self) -> tuple[str, ...]:
        """Retain the previous public list of open object names."""
        return tuple(item.name for item in self.open_objects)

    @property
    def insecure_ids(self) -> tuple[str, ...]:
        """Return all Access object IDs that are not secure."""
        return tuple(item.object_id for item in self.insecure_objects)

    @property
    def insecure_names(self) -> tuple[str, ...]:
        """Return all Access object names that are not secure."""
        return tuple(item.name for item in self.insecure_objects)

    @property
    def unavailable_ids(self) -> tuple[str, ...]:
        """Return Access object IDs with unavailable feedback."""
        return tuple(item.object_id for item in self.unavailable_objects)

    @property
    def unavailable_names(self) -> tuple[str, ...]:
        """Return Access object names with unavailable feedback."""
        return tuple(item.name for item in self.unavailable_objects)

    @property
    def attention_ids(self) -> tuple[str, ...]:
        """Return Access object IDs that require technical attention."""
        return tuple(item.object_id for item in self.attention_objects)

    @property
    def attention_names(self) -> tuple[str, ...]:
        """Return Access object names that require technical attention."""
        return tuple(item.name for item in self.attention_objects)

    @property
    def message(self) -> str:
        """Return one concise prioritized security message."""
        if self.unavailable_count:
            if self.unavailable_count == 1:
                return (
                    "Access-Rückmeldung nicht verfügbar: "
                    f"{self.unavailable_names[0]}."
                )
            return (
                f"{self.unavailable_count} Access-Rückmeldungen nicht "
                f"verfügbar: {', '.join(self.unavailable_names)}."
            )

        if self.attention_count:
            if self.attention_count == 1:
                return (
                    "Access-Zustand benötigt Aufmerksamkeit: "
                    f"{self.attention_names[0]}."
                )
            return (
                f"{self.attention_count} Access-Zustände benötigen "
                f"Aufmerksamkeit: {', '.join(self.attention_names)}."
            )

        if self.secure:
            return "Haus vollständig gesichert."

        if self.insecure_count == 1:
            return f"Haus nicht gesichert: {self.insecure_names[0]}."

        return (
            f"Haus nicht gesichert: {self.insecure_count} Access-Objekte "
            f"betroffen ({', '.join(self.insecure_names)})."
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "secure": self.secure,
            "all_access_available": self.all_access_available,
            "access_attention_required": self.access_attention_required,
            "alert": self.alert,
            "level": self.level,
            "open_count": self.open_count,
            "insecure_count": self.insecure_count,
            "unavailable_count": self.unavailable_count,
            "attention_count": self.attention_count,
            "opening_ids": list(self.opening_ids),
            "opening_names": list(self.opening_names),
            "insecure_ids": list(self.insecure_ids),
            "insecure_names": list(self.insecure_names),
            "unavailable_ids": list(self.unavailable_ids),
            "unavailable_names": list(self.unavailable_names),
            "attention_ids": list(self.attention_ids),
            "attention_names": list(self.attention_names),
            "message": self.message,
        }


class SecurityEngine:
    """Objective security evaluator independent from Home Assistant."""

    _ATTENTION_GARAGE_STATES = {
        "moving",
        "intermediate_open",
        "error",
    }

    @classmethod
    def evaluate(cls, access: AccessSnapshot) -> SecuritySnapshot:
        """Evaluate semantic house security from one Access snapshot."""
        objects = access.objects
        open_objects = tuple(item for item in objects if item.is_open)
        insecure_objects = tuple(item for item in objects if not item.secure)
        unavailable_objects = tuple(
            item for item in objects if not item.available
        )
        attention_objects = tuple(
            item
            for item in objects
            if (
                not item.available
                or (
                    item.opening_type == "garage_door"
                    and item.state in cls._ATTENTION_GARAGE_STATES
                )
            )
        )

        secure = access.all_secure and access.all_available
        all_access_available = access.all_available
        access_attention_required = bool(attention_objects)

        if not all_access_available:
            level = "error"
        elif access_attention_required:
            level = "attention"
        elif secure:
            level = "secure"
        else:
            level = "warning"

        return SecuritySnapshot(
            secure=secure,
            all_access_available=all_access_available,
            access_attention_required=access_attention_required,
            alert=not secure,
            level=level,
            open_count=len(open_objects),
            insecure_count=len(insecure_objects),
            unavailable_count=len(unavailable_objects),
            attention_count=len(attention_objects),
            open_objects=open_objects,
            insecure_objects=insecure_objects,
            unavailable_objects=unavailable_objects,
            attention_objects=attention_objects,
        )
