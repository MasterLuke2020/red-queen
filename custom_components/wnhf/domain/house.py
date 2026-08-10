"""WNHF house domain object."""

from __future__ import annotations

from dataclasses import dataclass

from .cover import Cover
from .light import Light
from .opening import Opening
from .room import Room


@dataclass(slots=True)
class House:
    """Platform-independent representation of a building."""

    object_id: str
    name: str
    rooms: dict[str, Room]
    lights: dict[str, Light]
    openings: dict[str, Opening]
    covers: dict[str, Cover]

    def room(self, room_id: str) -> Room:
        """Return a room by stable WNHF ID."""
        try:
            return self.rooms[room_id]
        except KeyError as err:
            raise KeyError(f"Unknown WNHF room id: {room_id}") from err

    def light(self, light_id: str) -> Light:
        """Return a light by stable WNHF ID."""
        try:
            return self.lights[light_id]
        except KeyError as err:
            raise KeyError(f"Unknown WNHF light id: {light_id}") from err

    def object(self, object_id: str) -> Room | Light:
        """Return any currently supported WNHF object by stable ID."""
        if object_id in self.rooms:
            return self.rooms[object_id]
        if object_id in self.lights:
            return self.lights[object_id]
        if object_id in self.openings:
            return self.openings[object_id]
        if object_id in self.covers:
            return self.covers[object_id]
        raise KeyError(f"Unknown WNHF object id: {object_id}")

    def list_rooms(self) -> list[dict]:
        """Return all rooms in stable order."""
        return [
            room.as_dict()
            for room in sorted(
                self.rooms.values(),
                key=lambda item: (
                    item.numeric_id if item.numeric_id is not None else 999999,
                    item.object_id,
                ),
            )
        ]

    def cover(self, cover_id: str) -> Cover:
        try:
            return self.covers[cover_id]
        except KeyError as err:
            raise KeyError(f"Unknown WNHF cover id: {cover_id}") from err

    def list_covers(self) -> list[dict]:
        return [cover.as_dict() for cover in sorted(self.covers.values(), key=lambda item: (item.room_id, item.object_id))]

    def opening(self, opening_id: str) -> Opening:
        """Return an opening by stable WNHF ID."""
        try:
            return self.openings[opening_id]
        except KeyError as err:
            raise KeyError(f"Unknown WNHF opening id: {opening_id}") from err

    def list_openings(self) -> list[dict]:
        """Return all openings in stable order."""
        return [
            opening.as_dict()
            for opening in sorted(
                self.openings.values(),
                key=lambda item: (item.room_id, item.object_id),
            )
        ]

    def list_lights(self) -> list[dict]:
        """Return all lights in stable order."""
        return [
            light.as_dict()
            for light in sorted(
                self.lights.values(),
                key=lambda item: (item.room_id, item.object_id),
            )
        ]

    @property
    def enabled_covers(self) -> tuple[Cover, ...]:
        return tuple(cover for cover in self.covers.values() if cover.enabled)

    @property
    def enabled_openings(self) -> tuple[Opening, ...]:
        """Return all enabled opening objects."""
        return tuple(
            opening for opening in self.openings.values() if opening.enabled
        )

    @property
    def enabled_lights(self) -> tuple[Light, ...]:
        """Return all enabled light objects."""
        return tuple(light for light in self.lights.values() if light.enabled)

    @property
    def controllable_lights(self) -> tuple[Light, ...]:
        """Return all safely controllable light objects."""
        return tuple(
            light for light in self.lights.values() if light.controllable
        )
