"""Registry loading, validation, and domain-model construction for WNHF."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .domain.cover import Cover
from .domain.house import House
from .domain.light import Light
from .domain.opening import DoorLock, DoorOpener, GarageDoor, Opening
from .domain.room import Room


class WNHFRegistryError(Exception):
    """Raised when a WNHF registry is invalid."""


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise WNHFRegistryError(f"Registry file not found: {path}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as err:
        raise WNHFRegistryError(f"Could not read {path}: {err}") from err

    if not isinstance(raw, dict):
        raise WNHFRegistryError(f"Root element in {path} must be a dictionary")

    return raw


def _load_rooms(path: Path) -> tuple[dict[str, Room], dict[str, Any]]:
    raw = _load_yaml(path)
    room_list = raw.get("rooms")

    if not isinstance(room_list, list):
        raise WNHFRegistryError(f"'rooms' in {path} must be a list")

    rooms: dict[str, Room] = {}
    numeric_ids: set[int] = set()

    for index, item in enumerate(room_list, start=1):
        if not isinstance(item, dict):
            raise WNHFRegistryError(f"Room entry #{index} must be a dictionary")

        room_id = item.get("id")
        name = item.get("name")
        numeric_id = item.get("numeric_id")
        floor_id = item.get("floor")
        room_type = item.get("type", "room")
        enabled = item.get("enabled", True)
        tags = item.get("tags", [])
        aliases = item.get("aliases", [])

        if not isinstance(room_id, str) or not room_id:
            raise WNHFRegistryError(f"Room entry #{index} has no valid 'id'")
        if room_id in rooms:
            raise WNHFRegistryError(f"Duplicate room id: {room_id}")
        if not isinstance(name, str) or not name:
            raise WNHFRegistryError(f"Room '{room_id}' has no valid 'name'")
        if not isinstance(floor_id, str) or not floor_id:
            raise WNHFRegistryError(f"Room '{room_id}' has no valid 'floor'")
        if not isinstance(room_type, str) or not room_type:
            raise WNHFRegistryError(f"Room '{room_id}' has no valid 'type'")
        if not isinstance(enabled, bool):
            raise WNHFRegistryError(
                f"Room '{room_id}': 'enabled' must be true or false"
            )
        if not isinstance(tags, list) or not all(
            isinstance(tag, str) for tag in tags
        ):
            raise WNHFRegistryError(
                f"Room '{room_id}': 'tags' must be a string list"
            )
        if not isinstance(aliases, list) or not all(
            isinstance(alias, str) for alias in aliases
        ):
            raise WNHFRegistryError(
                f"Room '{room_id}': 'aliases' must be a string list"
            )

        if numeric_id is not None:
            if not isinstance(numeric_id, int):
                raise WNHFRegistryError(
                    f"Room '{room_id}' has a non-integer numeric_id"
                )
            if numeric_id in numeric_ids:
                raise WNHFRegistryError(f"Duplicate room numeric_id: {numeric_id}")
            numeric_ids.add(numeric_id)

        rooms[room_id] = Room(
            object_id=room_id,
            numeric_id=numeric_id,
            name=name,
            floor_id=floor_id,
            room_type=room_type,
            enabled=enabled,
            tags=tuple(tags),
            aliases=tuple(aliases),
        )

    return rooms, raw


def _state_entities(item: dict[str, Any], object_id: str) -> tuple[str, ...]:
    entities: list[str] = []

    state = item.get("state")
    if state is not None:
        if not isinstance(state, dict):
            raise WNHFRegistryError(
                f"Light '{object_id}': 'state' must be a dictionary"
            )
        entity_id = state.get("entity_id")
        if entity_id is not None:
            if not isinstance(entity_id, str) or not entity_id:
                raise WNHFRegistryError(
                    f"Light '{object_id}': invalid state entity_id"
                )
            entities.append(entity_id)

    states = item.get("states", [])
    if not isinstance(states, list):
        raise WNHFRegistryError(
            f"Light '{object_id}': 'states' must be a list"
        )

    for state_item in states:
        if not isinstance(state_item, dict):
            raise WNHFRegistryError(
                f"Light '{object_id}': each states entry must be a dictionary"
            )
        entity_id = state_item.get("entity_id")
        if not isinstance(entity_id, str) or not entity_id:
            raise WNHFRegistryError(
                f"Light '{object_id}': invalid entity_id in states"
            )
        entities.append(entity_id)

    return tuple(dict.fromkeys(entities))


def _load_lights(
    path: Path,
    rooms: dict[str, Room],
) -> tuple[dict[str, Light], list[str]]:
    raw = _load_yaml(path)
    light_list = raw.get("lights")

    if not isinstance(light_list, list):
        raise WNHFRegistryError(f"'lights' in {path} must be a list")

    lights: dict[str, Light] = {}
    warnings: list[str] = []

    for index, item in enumerate(light_list, start=1):
        if not isinstance(item, dict):
            raise WNHFRegistryError(f"Light entry #{index} must be a dictionary")

        object_id = item.get("id")
        name = item.get("name")
        room_id = item.get("room")

        if not isinstance(object_id, str) or not object_id:
            raise WNHFRegistryError(f"Light entry #{index} has no valid 'id'")
        if object_id in lights:
            raise WNHFRegistryError(f"Duplicate light id: {object_id}")
        if not isinstance(name, str) or not name:
            raise WNHFRegistryError(f"Light '{object_id}' has no valid 'name'")
        if not isinstance(room_id, str) or room_id not in rooms:
            raise WNHFRegistryError(
                f"Light '{object_id}' references unknown room '{room_id}'"
            )

        enabled = item.get("enabled", True)
        if not isinstance(enabled, bool):
            raise WNHFRegistryError(
                f"Light '{object_id}': 'enabled' must be true or false"
            )

        control_mode = item.get("control_mode", "monitor_only")
        if control_mode not in {"toggle", "monitor_only", "reserved"}:
            raise WNHFRegistryError(
                f"Light '{object_id}': unsupported control_mode '{control_mode}'"
            )

        command_entity_id: str | None = None
        command = item.get("command")
        if command is not None:
            if not isinstance(command, dict):
                raise WNHFRegistryError(
                    f"Light '{object_id}': 'command' must be a dictionary"
                )
            command_entity_id = command.get("entity_id")
            if command_entity_id is not None and (
                not isinstance(command_entity_id, str) or not command_entity_id
            ):
                raise WNHFRegistryError(
                    f"Light '{object_id}': invalid command entity_id"
                )

        light = Light(
            object_id=object_id,
            name=name,
            room_id=room_id,
            enabled=enabled,
            control_mode=control_mode,
            command_entity_id=command_entity_id,
            state_entity_ids=_state_entities(item, object_id),
        )
        lights[object_id] = light
        rooms[room_id].add_light(light)

        if enabled and control_mode == "toggle" and not command_entity_id:
            warnings.append(
                f"Light '{object_id}' is toggle-controlled but has no command"
            )
        elif enabled and control_mode == "toggle" and not light.state_entity_ids:
            warnings.append(
                f"Light '{object_id}' is toggle-controlled but has no feedback"
            )

    return lights, warnings


def _required_string(mapping: dict[str, Any], key: str, object_id: str, section: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise WNHFRegistryError(f"Cover '{object_id}': invalid {section}.{key}")
    return value

def _load_covers(path: Path, rooms: dict[str, Room]) -> tuple[dict[str, Cover], list[str]]:
    raw = _load_yaml(path)
    cover_list = raw.get("covers")
    if not isinstance(cover_list, list):
        raise WNHFRegistryError(f"'covers' in {path} must be a list")
    covers: dict[str, Cover] = {}
    warnings: list[str] = []
    for index, item in enumerate(cover_list, start=1):
        if not isinstance(item, dict):
            raise WNHFRegistryError(f"Cover entry #{index} must be a dictionary")
        object_id=item.get("id"); name=item.get("name"); room_id=item.get("room")
        cover_type=item.get("type"); enabled=item.get("enabled",True)
        commands=item.get("commands"); feedback=item.get("feedback"); capabilities=item.get("capabilities")
        if not isinstance(object_id,str) or not object_id: raise WNHFRegistryError(f"Cover entry #{index} has no valid 'id'")
        if object_id in covers: raise WNHFRegistryError(f"Duplicate cover id: {object_id}")
        if not isinstance(name,str) or not name: raise WNHFRegistryError(f"Cover '{object_id}' has no valid 'name'")
        if not isinstance(room_id,str) or room_id not in rooms: raise WNHFRegistryError(f"Cover '{object_id}' references unknown room '{room_id}'")
        if cover_type != "venetian_blind": raise WNHFRegistryError(f"Cover '{object_id}' has unsupported type '{cover_type}'")
        if not isinstance(enabled,bool): raise WNHFRegistryError(f"Cover '{object_id}': 'enabled' must be true or false")
        if not isinstance(commands,dict): raise WNHFRegistryError(f"Cover '{object_id}': 'commands' must be a dictionary")
        if not isinstance(feedback,dict): raise WNHFRegistryError(f"Cover '{object_id}': 'feedback' must be a dictionary")
        if not isinstance(capabilities,list) or not capabilities or not all(isinstance(v,str) and v for v in capabilities):
            raise WNHFRegistryError(f"Cover '{object_id}' has no valid capabilities list")
        cover=Cover(
            object_id=object_id,name=name,room_id=room_id,cover_type=cover_type,enabled=enabled,
            open_command_entity_id=_required_string(commands,"open_entity_id",object_id,"commands"),
            close_command_entity_id=_required_string(commands,"close_entity_id",object_id,"commands"),
            blades_open_command_entity_id=_required_string(commands,"blades_open_entity_id",object_id,"commands"),
            blades_close_command_entity_id=_required_string(commands,"blades_close_entity_id",object_id,"commands"),
            open_feedback_entity_id=_required_string(feedback,"open_entity_id",object_id,"feedback"),
            closed_feedback_entity_id=_required_string(feedback,"closed_entity_id",object_id,"feedback"),
            opening_feedback_entity_id=_required_string(feedback,"opening_entity_id",object_id,"feedback"),
            closing_feedback_entity_id=_required_string(feedback,"closing_entity_id",object_id,"feedback"),
            capabilities=tuple(capabilities))
        covers[object_id]=cover; rooms[room_id].add_cover(cover)
    return covers,warnings


def _optional_enabled_section(
    item: dict[str, Any],
    key: str,
    object_id: str,
) -> dict[str, Any] | None:
    """Return one optional enabled configuration section."""
    section = item.get(key)

    if section is None:
        return None

    if not isinstance(section, dict):
        raise WNHFRegistryError(
            f"Opening '{object_id}': '{key}' must be a dictionary"
        )

    enabled = section.get("enabled", True)
    if not isinstance(enabled, bool):
        raise WNHFRegistryError(
            f"Opening '{object_id}': '{key}.enabled' must be true or false"
        )

    return section if enabled else None


def _optional_entity_id(
    mapping: dict[str, Any],
    key: str,
    object_id: str,
    section: str,
) -> str | None:
    """Return and validate one optional Home Assistant entity ID."""
    value = mapping.get(key)

    if value is None:
        return None

    if not isinstance(value, str) or not value:
        raise WNHFRegistryError(
            f"Opening '{object_id}': invalid {section}.{key}"
        )

    return value


def _parse_door_lock(
    item: dict[str, Any],
    object_id: str,
    opening_type: str,
) -> DoorLock | None:
    """Parse the optional lock module of a normal door."""
    section = _optional_enabled_section(item, "lock", object_id)
    if section is None:
        return None

    if opening_type != "door":
        raise WNHFRegistryError(
            f"Opening '{object_id}': 'lock' is supported only for type 'door'"
        )

    feedback = section.get("feedback")
    if not isinstance(feedback, dict):
        raise WNHFRegistryError(
            f"Opening '{object_id}': 'lock.feedback' must be a dictionary"
        )

    feedback_entity_id = _optional_entity_id(
        feedback,
        "entity_id",
        object_id,
        "lock.feedback",
    )
    if feedback_entity_id is None:
        raise WNHFRegistryError(
            f"Opening '{object_id}': lock requires feedback.entity_id"
        )

    locked_states = feedback.get("locked_states", ["on", "locked"])
    if not isinstance(locked_states, list) or not locked_states or not all(
        isinstance(value, str) and value for value in locked_states
    ):
        raise WNHFRegistryError(
            f"Opening '{object_id}': lock.feedback.locked_states must be "
            "a non-empty string list"
        )

    commands = section.get("commands", {})
    if not isinstance(commands, dict):
        raise WNHFRegistryError(
            f"Opening '{object_id}': 'lock.commands' must be a dictionary"
        )

    return DoorLock(
        feedback_entity_id=feedback_entity_id,
        locked_states=tuple(locked_states),
        lock_command_entity_id=_optional_entity_id(
            commands,
            "lock_entity_id",
            object_id,
            "lock.commands",
        ),
        unlock_command_entity_id=_optional_entity_id(
            commands,
            "unlock_entity_id",
            object_id,
            "lock.commands",
        ),
    )


def _parse_door_opener(
    item: dict[str, Any],
    object_id: str,
    opening_type: str,
) -> DoorOpener | None:
    """Parse the optional electric door opener."""
    section = _optional_enabled_section(item, "door_opener", object_id)
    if section is None:
        return None

    if opening_type != "door":
        raise WNHFRegistryError(
            f"Opening '{object_id}': 'door_opener' is supported only for "
            "type 'door'"
        )

    command = section.get("command")
    if not isinstance(command, dict):
        raise WNHFRegistryError(
            f"Opening '{object_id}': 'door_opener.command' must be a "
            "dictionary"
        )

    command_entity_id = _optional_entity_id(
        command,
        "entity_id",
        object_id,
        "door_opener.command",
    )
    if command_entity_id is None:
        raise WNHFRegistryError(
            f"Opening '{object_id}': door opener requires command.entity_id"
        )

    return DoorOpener(command_entity_id=command_entity_id)


def _parse_garage_door(
    item: dict[str, Any],
    object_id: str,
    opening_type: str,
) -> GarageDoor | None:
    """Parse the dedicated two-sensor garage-door configuration."""
    section = _optional_enabled_section(item, "garage", object_id)
    if section is None:
        return None

    if opening_type != "garage_door":
        raise WNHFRegistryError(
            f"Opening '{object_id}': 'garage' is supported only for type "
            "'garage_door'"
        )

    feedback = section.get("feedback")
    if not isinstance(feedback, dict):
        raise WNHFRegistryError(
            f"Opening '{object_id}': 'garage.feedback' must be a dictionary"
        )

    open_feedback_entity_id = _optional_entity_id(
        feedback,
        "open_entity_id",
        object_id,
        "garage.feedback",
    )
    closed_feedback_entity_id = _optional_entity_id(
        feedback,
        "closed_entity_id",
        object_id,
        "garage.feedback",
    )

    if open_feedback_entity_id is None or closed_feedback_entity_id is None:
        raise WNHFRegistryError(
            f"Opening '{object_id}': garage requires both open_entity_id "
            "and closed_entity_id feedback"
        )

    command = section.get("command")
    if not isinstance(command, dict):
        raise WNHFRegistryError(
            f"Opening '{object_id}': 'garage.command' must be a dictionary"
        )

    toggle_command_entity_id = _optional_entity_id(
        command,
        "toggle_entity_id",
        object_id,
        "garage.command",
    )
    if toggle_command_entity_id is None:
        raise WNHFRegistryError(
            f"Opening '{object_id}': garage requires command.toggle_entity_id"
        )

    movement_timeout_seconds = section.get(
        "movement_timeout_seconds",
        25.0,
    )
    if (
        not isinstance(movement_timeout_seconds, (int, float))
        or isinstance(movement_timeout_seconds, bool)
        or movement_timeout_seconds <= 0
    ):
        raise WNHFRegistryError(
            f"Opening '{object_id}': garage movement_timeout_seconds must "
            "be a positive number"
        )

    return GarageDoor(
        open_feedback_entity_id=open_feedback_entity_id,
        closed_feedback_entity_id=closed_feedback_entity_id,
        toggle_command_entity_id=toggle_command_entity_id,
        stop_command_entity_id=_optional_entity_id(
            command,
            "stop_entity_id",
            object_id,
            "garage.command",
        ),
        movement_timeout_seconds=float(movement_timeout_seconds),
    )

def _load_openings(
    path: Path,
    rooms: dict[str, Room],
) -> tuple[dict[str, Opening], list[str]]:
    raw = _load_yaml(path)
    opening_list = raw.get("openings")

    if not isinstance(opening_list, list):
        raise WNHFRegistryError(f"'openings' in {path} must be a list")

    openings: dict[str, Opening] = {}
    warnings: list[str] = []

    for index, item in enumerate(opening_list, start=1):
        if not isinstance(item, dict):
            raise WNHFRegistryError(
                f"Opening entry #{index} must be a dictionary"
            )

        object_id = item.get("id")
        name = item.get("name")
        room_id = item.get("room")
        opening_type = item.get("type")
        enabled = item.get("enabled", True)
        state = item.get("state")

        if not isinstance(object_id, str) or not object_id:
            raise WNHFRegistryError(
                f"Opening entry #{index} has no valid 'id'"
            )
        if object_id in openings:
            raise WNHFRegistryError(f"Duplicate opening id: {object_id}")
        if not isinstance(name, str) or not name:
            raise WNHFRegistryError(
                f"Opening '{object_id}' has no valid 'name'"
            )
        if not isinstance(room_id, str) or room_id not in rooms:
            raise WNHFRegistryError(
                f"Opening '{object_id}' references unknown room '{room_id}'"
            )
        if opening_type not in {
            "window",
            "door",
            "sliding_door",
            "garage_door",
        }:
            raise WNHFRegistryError(
                f"Opening '{object_id}' has unsupported type "
                f"'{opening_type}'"
            )
        if not isinstance(enabled, bool):
            raise WNHFRegistryError(
                f"Opening '{object_id}': 'enabled' must be true or false"
            )

        garage_door = _parse_garage_door(
            item,
            object_id,
            opening_type,
        )

        state_entity_id: str | None = None
        open_states: tuple[str, ...] = ()

        if state is not None:
            if not isinstance(state, dict):
                raise WNHFRegistryError(
                    f"Opening '{object_id}': 'state' must be a dictionary"
                )

            state_entity_id = _optional_entity_id(
                state,
                "entity_id",
                object_id,
                "state",
            )
            open_state_values = state.get("open_states")

            if state_entity_id is None:
                raise WNHFRegistryError(
                    f"Opening '{object_id}' has no valid state entity_id"
                )
            if (
                not isinstance(open_state_values, list)
                or not open_state_values
                or not all(
                    isinstance(value, str) and value
                    for value in open_state_values
                )
            ):
                raise WNHFRegistryError(
                    f"Opening '{object_id}' has no valid open_states list"
                )

            open_states = tuple(open_state_values)

        elif garage_door is None:
            raise WNHFRegistryError(
                f"Opening '{object_id}': 'state' is required unless a "
                "dedicated garage configuration is present"
            )

        lock = _parse_door_lock(
            item,
            object_id,
            opening_type,
        )
        door_opener = _parse_door_opener(
            item,
            object_id,
            opening_type,
        )

        opening = Opening(
            object_id=object_id,
            name=name,
            room_id=room_id,
            opening_type=opening_type,
            enabled=enabled,
            state_entity_id=state_entity_id,
            open_states=open_states,
            lock=lock,
            door_opener=door_opener,
            garage_door=garage_door,
        )
        openings[object_id] = opening
        rooms[room_id].add_opening(opening)

        if enabled and opening_type == "door" and lock is not None:
            if (
                lock.lock_command_entity_id is None
                and lock.unlock_command_entity_id is None
            ):
                warnings.append(
                    f"Opening '{object_id}' has lock feedback but no lock "
                    "or unlock command"
                )
        elif enabled and opening_type == "garage_door" and garage_door is None:
            warnings.append(
                f"Opening '{object_id}' uses legacy single-state garage "
                "monitoring"
            )

    return openings, warnings


def load_house(registry_dir: Path) -> tuple[House, tuple[str, ...]]:
    """Load, validate, and build the WNHF house domain model."""
    rooms, rooms_raw = _load_rooms(registry_dir / "rooms.yaml")
    lights, light_warnings = _load_lights(
        registry_dir / "lights.yaml", rooms
    )
    openings, opening_warnings = _load_openings(
        registry_dir / "openings.yaml", rooms
    )
    covers, cover_warnings = _load_covers(registry_dir / "covers.yaml", rooms)
    warnings = [*light_warnings, *opening_warnings, *cover_warnings]

    building = rooms_raw.get("building", {})
    house_id = building.get("id", "house")
    house_name = building.get("name", "Red Queen House")

    if not isinstance(house_id, str) or not house_id:
        raise WNHFRegistryError("Building has no valid 'id'")
    if not isinstance(house_name, str) or not house_name:
        raise WNHFRegistryError("Building has no valid 'name'")

    return (
        House(
            object_id=house_id,
            name=house_name,
            rooms=rooms,
            lights=lights,
            openings=openings,
            covers=covers,
        ),
        tuple(warnings),
    )
