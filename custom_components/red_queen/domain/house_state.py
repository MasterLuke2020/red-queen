"""Aggregated runtime state for the complete WNHF house."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class HouseState(StrEnum):
    """Normalized overall building states."""

    READY = "ready"
    ACTIVITY = "activity"
    ATTENTION = "attention"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class HouseSnapshot:
    """Immutable aggregate snapshot of the complete building."""

    house_id: str
    house_name: str
    state: HouseState
    secure: bool
    all_access_available: bool
    access_attention_required: bool
    access_insecure_count: int
    access_unavailable_count: int
    access_attention_count: int
    access_insecure_ids: tuple[str, ...]
    access_insecure_names: tuple[str, ...]
    access_unavailable_ids: tuple[str, ...]
    access_unavailable_names: tuple[str, ...]
    access_attention_ids: tuple[str, ...]
    access_attention_names: tuple[str, ...]
    validation_status: str
    quality_score: int

    lights_on_count: int
    light_ids_on: tuple[str, ...]
    light_names_on: tuple[str, ...]

    openings_open_count: int
    opening_ids_open: tuple[str, ...]
    opening_names_open: tuple[str, ...]

    covers_opening_count: int
    covers_closing_count: int
    covers_moving_count: int
    covers_error_count: int
    cover_ids_moving: tuple[str, ...]
    cover_names_moving: tuple[str, ...]
    cover_ids_error: tuple[str, ...]

    @property
    def has_activity(self) -> bool:
        return self.lights_on_count > 0 or self.covers_moving_count > 0

    @property
    def requires_attention(self) -> bool:
        return not self.secure or self.access_attention_required

    @property
    def has_error(self) -> bool:
        return (
            self.validation_status == "error"
            or self.covers_error_count > 0
            or not self.all_access_available
        )

    @property
    def message(self) -> str:
        """Return one prioritized human-readable house message."""
        if self.has_error:
            parts: list[str] = []
            if self.validation_status == "error":
                parts.append("Framework-Validierung fehlerhaft")
            if self.covers_error_count:
                parts.append(
                    f"{self.covers_error_count} Raffstore mit Statusfehler"
                )
            if not self.all_access_available:
                parts.append(
                    f"{self.access_unavailable_count} Access-Rückmeldung "
                    "nicht verfügbar"
                )
            return "Fehler: " + ", ".join(parts) + "."

        if self.access_attention_required:
            if self.access_attention_count == 1:
                return (
                    "Access-Zustand benötigt Aufmerksamkeit: "
                    f"{self.access_attention_names[0]}."
                )
            return (
                f"{self.access_attention_count} Access-Zustände benötigen "
                f"Aufmerksamkeit: "
                f"{', '.join(self.access_attention_names)}."
            )

        if not self.secure:
            if self.access_insecure_count == 1:
                return (
                    "Haus nicht gesichert: "
                    f"{self.access_insecure_names[0]}."
                )
            return (
                f"Haus nicht gesichert: {self.access_insecure_count} "
                f"Access-Objekte betroffen "
                f"({', '.join(self.access_insecure_names)})."
            )

        if self.openings_open_count:
            if self.openings_open_count == 1:
                return (
                    f"1 Öffnung offen: {self.opening_names_open[0]}."
                )
            return (
                f"{self.openings_open_count} Öffnungen offen: "
                f"{', '.join(self.opening_names_open)}."
            )

        activity: list[str] = []
        if self.lights_on_count:
            activity.append(
                "1 Licht eingeschaltet"
                if self.lights_on_count == 1
                else f"{self.lights_on_count} Lichter eingeschaltet"
            )
        if self.covers_moving_count:
            activity.append(
                "1 Raffstore in Bewegung"
                if self.covers_moving_count == 1
                else f"{self.covers_moving_count} Raffstores in Bewegung"
            )

        if activity:
            return ", ".join(activity) + "."

        return "Haus bereit. Alle Öffnungen geschlossen, keine Aktivität."

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "house_id": self.house_id,
            "house_name": self.house_name,
            "state": self.state.value,
            "message": self.message,
            "secure": self.secure,
            "all_access_available": self.all_access_available,
            "access_attention_required": self.access_attention_required,
            "has_activity": self.has_activity,
            "requires_attention": self.requires_attention,
            "has_error": self.has_error,
            "validation": {
                "status": self.validation_status,
                "quality_score": self.quality_score,
            },
            "lighting": {
                "count_on": self.lights_on_count,
                "ids_on": list(self.light_ids_on),
                "names_on": list(self.light_names_on),
            },
            "access": {
                "secured": self.secure,
                "all_available": self.all_access_available,
                "attention_required": self.access_attention_required,
                "insecure_count": self.access_insecure_count,
                "unavailable_count": self.access_unavailable_count,
                "attention_count": self.access_attention_count,
                "insecure_ids": list(self.access_insecure_ids),
                "insecure_names": list(self.access_insecure_names),
                "unavailable_ids": list(self.access_unavailable_ids),
                "unavailable_names": list(self.access_unavailable_names),
                "attention_ids": list(self.access_attention_ids),
                "attention_names": list(self.access_attention_names),
            },
            "openings": {
                "count_open": self.openings_open_count,
                "ids_open": list(self.opening_ids_open),
                "names_open": list(self.opening_names_open),
            },
            "covers": {
                "opening": self.covers_opening_count,
                "closing": self.covers_closing_count,
                "moving": self.covers_moving_count,
                "errors": self.covers_error_count,
                "ids_moving": list(self.cover_ids_moving),
                "names_moving": list(self.cover_names_moving),
                "ids_error": list(self.cover_ids_error),
            },
        }
