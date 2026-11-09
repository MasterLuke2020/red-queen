"""Semantic plant-care domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any


@dataclass(frozen=True, slots=True)
class Plant:
    """Installation-owned plant definition without provider coupling."""

    object_id: str
    name: str
    species: str
    room_id: str
    location: str
    watering_interval_days: int
    enabled: bool = True
    moisture_sensor_entity_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.object_id,
            "object_type": "plant",
            "name": self.name,
            "species": self.species,
            "room_id": self.room_id,
            "location": self.location,
            "watering_interval_days": self.watering_interval_days,
            "enabled": self.enabled,
            "moisture_sensor_entity_id": self.moisture_sensor_entity_id,
            "sensor_configured": self.moisture_sensor_entity_id is not None,
            "capabilities": ["plants.monitor_care", "plants.record_watering"],
        }


@dataclass(frozen=True, slots=True)
class PlantCareSnapshot:
    """Calculated watering state for exactly one semantic plant."""

    plant: Plant
    generated_at: datetime
    last_watered_at: datetime | None
    watering_count: int

    @property
    def due_at(self) -> datetime | None:
        if self.last_watered_at is None:
            return None
        return self.last_watered_at + timedelta(
            days=self.plant.watering_interval_days
        )

    @property
    def status(self) -> str:
        due_at = self.due_at
        if due_at is None:
            return "unknown"
        if self.generated_at < due_at:
            return "ok"
        if self.generated_at < due_at + timedelta(days=1):
            return "due"
        return "overdue"

    @property
    def days_until_due(self) -> int | None:
        due_at = self.due_at
        if due_at is None:
            return None
        seconds = (due_at - self.generated_at).total_seconds()
        if seconds >= 0:
            return int((seconds + 86399) // 86400)
        return -int((-seconds) // 86400)

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.plant.as_dict(),
            "generated_at": self.generated_at.astimezone(UTC).isoformat(),
            "status": self.status,
            "last_watered_at": (
                self.last_watered_at.astimezone(UTC).isoformat()
                if self.last_watered_at is not None
                else None
            ),
            "due_at": (
                self.due_at.astimezone(UTC).isoformat()
                if self.due_at is not None
                else None
            ),
            "days_until_due": self.days_until_due,
            "watering_count": self.watering_count,
            "objective_moisture_available": False,
            "care_state_claimed_without_history": False,
        }
