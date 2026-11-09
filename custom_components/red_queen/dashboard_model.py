"""Platform-independent dashboard model for Red Queen.

RC12 intentionally separates the semantic dashboard model from the Home Assistant
Lovelace adapter.  This module knows the Red Queen house model, but it does not
know entity IDs, Lovelace storage internals, cards, or frontend implementation
specifics.

The split gives us a stable contract:

    Red Queen House -> DashboardModel -> HA entity binding -> Lovelace rendering

Only enabled objects that have a native Red Queen representation are included.
Provider entities (PLC, MQTT, OPC UA, etc.) never become dashboard objects here.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, Mapping

from .domain.house import House
from .domain.room import Room


DASHBOARD_CONTRACT_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class DashboardFloorDescriptor:
    """Optional Home Assistant floor metadata used for display and ordering."""

    floor_id: str
    name: str
    order: int | None = None


@dataclass(frozen=True, slots=True)
class DashboardLightSpec:
    """One native Red Queen light shown in a room view."""

    object_id: str
    name: str
    room_id: str
    capabilities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DashboardCoverSpec:
    """One native Red Queen venetian blind shown in a room view."""

    object_id: str
    name: str
    room_id: str
    capabilities: tuple[str, ...]
    position_feedback: bool
    blade_commands: bool


@dataclass(frozen=True, slots=True)
class DashboardOpeningSpec:
    """One native Red Queen opening/access object shown in a room view."""

    object_id: str
    name: str
    room_id: str
    opening_type: str
    capabilities: tuple[str, ...]
    has_lock: bool
    has_door_opener: bool
    is_garage_door: bool
    garage_stop_supported: bool


@dataclass(frozen=True, slots=True)
class DashboardPlantSpec:
    """One native Red Queen Plant Care object shown in a room view."""

    object_id: str
    name: str
    room_id: str
    species: str
    location: str
    watering_interval_days: int


@dataclass(frozen=True, slots=True)
class DashboardRoomSpec:
    """Dashboard-ready semantic room without Home Assistant entity IDs."""

    object_id: str
    name: str
    floor_id: str
    path: str
    lights: tuple[DashboardLightSpec, ...]
    covers: tuple[DashboardCoverSpec, ...]
    openings: tuple[DashboardOpeningSpec, ...]
    plants: tuple[DashboardPlantSpec, ...]

    @property
    def has_content(self) -> bool:
        """Return whether the room has at least one dashboard object."""
        return bool(self.lights or self.covers or self.openings or self.plants)

    @property
    def object_count(self) -> int:
        """Return the number of semantic objects represented by the room."""
        return len(self.lights) + len(self.covers) + len(self.openings) + len(self.plants)


@dataclass(frozen=True, slots=True)
class DashboardFloorSpec:
    """One floor view and its enabled Red Queen rooms."""

    floor_id: str
    name: str
    path: str
    order: int | None
    rooms: tuple[DashboardRoomSpec, ...]


@dataclass(frozen=True, slots=True)
class DashboardFeatureFlags:
    """Top-level features used to decide which overview sections exist."""

    lights: bool
    covers: bool
    openings: bool
    access: bool
    garage: bool
    plants: bool


@dataclass(frozen=True, slots=True)
class DashboardCounts:
    """Deterministic semantic counts used by configurator status and metadata."""

    floors: int
    rooms: int
    lights: int
    covers: int
    openings: int
    garages: int
    plants: int


@dataclass(frozen=True, slots=True)
class DashboardModel:
    """Complete platform-independent Red Queen dashboard model."""

    contract_version: str
    house_id: str
    house_name: str
    overview_path: str
    plants_path: str | None
    system_path: str
    floors: tuple[DashboardFloorSpec, ...]
    features: DashboardFeatureFlags
    counts: DashboardCounts

    @property
    def rooms(self) -> tuple[DashboardRoomSpec, ...]:
        """Return all rooms in final deterministic dashboard order."""
        return tuple(room for floor in self.floors for room in floor.rooms)


_PATH_RE = re.compile(r"[^a-z0-9]+")


def _stable_path(prefix: str, value: str) -> str:
    """Build a deterministic URL-safe path from a stable semantic ID."""
    normalized = _PATH_RE.sub("-", value.casefold()).strip("-")
    return f"{prefix}-{normalized}" if normalized else prefix


def _fallback_floor_name(floor_id: str) -> str:
    """Return a readable fallback when no HA floor display metadata is available.

    Manual registries often use semantic ids such as ``house.eg`` instead of a
    Home Assistant Floor Registry id.  The dashboard must never expose that
    implementation detail as ``House.Eg``.  Common floor segments receive a
    stable human label; unknown ids are still converted deterministically.
    """
    raw = floor_id.strip()
    segment = raw.rsplit(".", 1)[-1].casefold() if raw else ""
    aliases = {
        "eg": "Erdgeschoss",
        "ground": "Erdgeschoss",
        "ground_floor": "Erdgeschoss",
        "og": "Obergeschoss",
        "upper": "Obergeschoss",
        "upper_floor": "Obergeschoss",
        "ug": "Untergeschoss",
        "basement": "Keller",
        "keller": "Keller",
        "dg": "Dachgeschoss",
        "attic": "Dachgeschoss",
        "outdoor": "Außenbereich",
        "outside": "Außenbereich",
        "aussen": "Außenbereich",
        "außen": "Außenbereich",
        "unassigned": "Weitere Räume",
    }
    if segment in aliases:
        return aliases[segment]

    display_source = raw.rsplit(".", 1)[-1] if "." in raw else raw
    words = re.sub(r"[_-]+", " ", display_source).strip()
    return words.title() if words else "Weitere Räume"


def _room_sort_key(room: Room) -> tuple[int, int, str, str]:
    """Sort numeric room IDs first, then fall back to stable human/name ordering."""
    if room.numeric_id is not None:
        return (0, room.numeric_id, room.name.casefold(), room.object_id)
    return (1, 0, room.name.casefold(), room.object_id)


def _descriptor_map(
    descriptors: Iterable[DashboardFloorDescriptor] | None,
) -> Mapping[str, DashboardFloorDescriptor]:
    if descriptors is None:
        return {}
    return {descriptor.floor_id: descriptor for descriptor in descriptors}


def _build_room(room: Room) -> DashboardRoomSpec:
    """Compile one enabled semantic room into the dashboard-neutral model."""
    lights = tuple(
        DashboardLightSpec(
            object_id=light.object_id,
            name=light.name,
            room_id=light.room_id,
            capabilities=tuple(light.supported_capability_ids),
        )
        for light in sorted(
            (item for item in room.lights if item.controllable),
            key=lambda item: (item.name.casefold(), item.object_id),
        )
    )

    covers = tuple(
        DashboardCoverSpec(
            object_id=cover.object_id,
            name=cover.name,
            room_id=cover.room_id,
            capabilities=tuple(cover.supported_capability_ids),
            position_feedback=bool(cover.closed_percent_feedback_entity_id),
            blade_commands=all(
                capability in cover.supported_capability_ids
                for capability in ("covers.blades_open", "covers.blades_close")
            ),
        )
        for cover in sorted(
            (item for item in room.covers if item.enabled),
            key=lambda item: (item.name.casefold(), item.object_id),
        )
    )

    openings = tuple(
        DashboardOpeningSpec(
            object_id=opening.object_id,
            name=opening.name,
            room_id=opening.room_id,
            opening_type=opening.opening_type,
            capabilities=tuple(opening.supported_capability_ids),
            has_lock=opening.lock is not None,
            has_door_opener=opening.door_opener is not None,
            is_garage_door=opening.garage_door is not None,
            garage_stop_supported=(
                opening.garage_door is not None
                and opening.garage_door.stop_command_entity_id is not None
            ),
        )
        for opening in sorted(
            (item for item in room.openings if item.enabled),
            key=lambda item: (item.name.casefold(), item.object_id),
        )
    )

    plants = tuple(
        DashboardPlantSpec(
            object_id=plant.object_id,
            name=plant.name,
            room_id=plant.room_id,
            species=plant.species,
            location=plant.location,
            watering_interval_days=plant.watering_interval_days,
        )
        for plant in sorted(
            (item for item in room.plants if item.enabled),
            key=lambda item: (item.name.casefold(), item.object_id),
        )
    )

    return DashboardRoomSpec(
        object_id=room.object_id,
        name=room.name,
        floor_id=room.floor_id,
        path=_stable_path("room", room.object_id),
        lights=lights,
        covers=covers,
        openings=openings,
        plants=plants,
    )


def build_dashboard_model(
    house: House,
    *,
    floor_descriptors: Iterable[DashboardFloorDescriptor] | None = None,
) -> DashboardModel:
    """Compile a Red Queen ``House`` into the stable RC12 dashboard model.

    ``floor_descriptors`` is deliberately optional.  The Home Assistant adapter
    can provide real Floor Registry display names and ordering.  Manual/legacy
    registries still receive a deterministic fallback based on ``Room.floor_id``.
    """
    descriptors = _descriptor_map(floor_descriptors)

    rooms_by_floor: dict[str, list[Room]] = {}
    for room in house.rooms.values():
        if not room.enabled:
            continue
        rooms_by_floor.setdefault(room.floor_id, []).append(room)

    floors: list[DashboardFloorSpec] = []
    for floor_id, source_rooms in rooms_by_floor.items():
        descriptor = descriptors.get(floor_id)
        floor_name = descriptor.name if descriptor is not None else _fallback_floor_name(floor_id)
        floor_order = descriptor.order if descriptor is not None else None
        room_specs = tuple(
            _build_room(room)
            for room in sorted(source_rooms, key=_room_sort_key)
        )
        floors.append(
            DashboardFloorSpec(
                floor_id=floor_id,
                name=floor_name,
                path=_stable_path("floor", floor_id),
                order=floor_order,
                rooms=room_specs,
            )
        )

    floors.sort(
        key=lambda floor: (
            floor.order is None,
            floor.order if floor.order is not None else 0,
            floor.name.casefold(),
            floor.floor_id,
        )
    )

    all_rooms = tuple(room for floor in floors for room in floor.rooms)
    lights = tuple(light for room in all_rooms for light in room.lights)
    covers = tuple(cover for room in all_rooms for cover in room.covers)
    openings = tuple(opening for room in all_rooms for opening in room.openings)
    plants = tuple(plant for room in all_rooms for plant in room.plants)

    garage_count = sum(opening.is_garage_door for opening in openings)
    access_present = any(
        opening.has_lock or opening.has_door_opener or opening.is_garage_door
        for opening in openings
    )

    return DashboardModel(
        contract_version=DASHBOARD_CONTRACT_VERSION,
        house_id=house.object_id,
        house_name=house.name,
        overview_path="overview",
        plants_path="plants" if plants else None,
        system_path="system",
        floors=tuple(floors),
        features=DashboardFeatureFlags(
            lights=bool(lights),
            covers=bool(covers),
            openings=bool(openings),
            access=access_present,
            garage=garage_count > 0,
            plants=bool(plants),
        ),
        counts=DashboardCounts(
            floors=len(floors),
            rooms=len(all_rooms),
            lights=len(lights),
            covers=len(covers),
            openings=len(openings),
            garages=garage_count,
            plants=len(plants),
        ),
    )
