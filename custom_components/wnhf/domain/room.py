"""WNHF room domain object."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .cover import Cover
from .light import Light
from .opening import Opening
from .plant import Plant


@dataclass(slots=True)
class Room:
    """A platform-independent room object."""

    object_id: str
    numeric_id: int | None
    name: str
    floor_id: str
    room_type: str
    enabled: bool
    tags: tuple[str, ...]
    aliases: tuple[str, ...]
    _lights: list[Light] = field(default_factory=list, repr=False)
    _openings: list[Opening] = field(default_factory=list, repr=False)
    _covers: list[Cover] = field(default_factory=list, repr=False)
    _plants: list[Plant] = field(default_factory=list, repr=False)

    @property
    def lights(self) -> tuple[Light, ...]:
        """Return all light objects assigned to this room."""
        return tuple(self._lights)

    @property
    def covers(self) -> tuple[Cover, ...]:
        return tuple(self._covers)

    def add_cover(self, cover: Cover) -> None:
        if cover.room_id != self.object_id:
            raise ValueError(f"Cover '{cover.object_id}' does not belong to room '{self.object_id}'")
        self._covers.append(cover)

    @property
    def openings(self) -> tuple[Opening, ...]:
        """Return all opening objects assigned to this room."""
        return tuple(self._openings)

    def add_opening(self, opening: Opening) -> None:
        """Attach an opening to this room."""
        if opening.room_id != self.object_id:
            raise ValueError(
                f"Opening '{opening.object_id}' does not belong to room "
                f"'{self.object_id}'"
            )
        self._openings.append(opening)

    def add_light(self, light: Light) -> None:
        """Attach a light to this room."""
        if light.room_id != self.object_id:
            raise ValueError(
                f"Light '{light.object_id}' does not belong to room "
                f"'{self.object_id}'"
            )
        self._lights.append(light)

    @property
    def plants(self) -> tuple[Plant, ...]:
        return tuple(self._plants)

    def add_plant(self, plant: Plant) -> None:
        if plant.room_id != self.object_id:
            raise ValueError(
                f"Plant '{plant.object_id}' does not belong to room "
                f"'{self.object_id}'"
            )
        self._plants.append(plant)


    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation for the Registry Explorer."""
        return {
            "id": self.object_id,
            "object_type": "room",
            "numeric_id": self.numeric_id,
            "name": self.name,
            "floor_id": self.floor_id,
            "room_type": self.room_type,
            "enabled": self.enabled,
            "tags": list(self.tags),
            "aliases": list(self.aliases),
            "light_count": len(self._lights),
            "light_ids": [light.object_id for light in self._lights],
            "opening_count": len(self._openings),
            "opening_ids": [opening.object_id for opening in self._openings],
            "cover_count": len(self._covers),
            "cover_ids": [cover.object_id for cover in self._covers],
            "plant_count": len(self._plants),
            "plant_ids": [plant.object_id for plant in self._plants],
            "capabilities": ["contains_objects"],
        }
