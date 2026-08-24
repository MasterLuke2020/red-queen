"""Pure Lovelace renderer for the Red Queen RC12 dashboard.

The renderer is deliberately side-effect free.  It receives the semantic
``DashboardModel`` and the resolved native ``DashboardBindings`` and produces a
plain Home Assistant Lovelace configuration dictionary.

No Home Assistant storage API is used here.  The storage/installation adapter
will be a separate RC12 work package so the generated dashboard can be tested,
serialized and hashed independently from Home Assistant's internal dashboard
persistence implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from .dashboard_binding import (
    DashboardBindings,
    DashboardCoverBinding,
    DashboardOpeningBinding,
    DashboardPlantBinding,
)
from .dashboard_model import (
    DashboardFloorSpec,
    DashboardModel,
    DashboardOpeningSpec,
    DashboardRoomSpec,
)


DASHBOARD_RENDERER_CONTRACT_VERSION = "1.0"
DEFAULT_DASHBOARD_URL_PATH = "red-queen"


@dataclass(frozen=True, slots=True)
class DashboardRenderMetadata:
    """Deterministic metadata describing one rendered dashboard."""

    renderer_contract_version: str
    model_contract_version: str
    binding_contract_version: str
    config_sha256: str
    view_count: int
    floor_view_count: int
    room_view_count: int
    unresolved_binding_count: int

    def as_dict(self) -> dict[str, Any]:
        """Return JSON-serializable renderer metadata."""
        return {
            "renderer_contract_version": self.renderer_contract_version,
            "model_contract_version": self.model_contract_version,
            "binding_contract_version": self.binding_contract_version,
            "config_sha256": self.config_sha256,
            "view_count": self.view_count,
            "floor_view_count": self.floor_view_count,
            "room_view_count": self.room_view_count,
            "unresolved_binding_count": self.unresolved_binding_count,
        }


@dataclass(frozen=True, slots=True)
class DashboardRenderResult:
    """Rendered Lovelace configuration plus deterministic metadata."""

    config: dict[str, Any]
    metadata: DashboardRenderMetadata


def _entity_tile(
    entity_id: str,
    *,
    name: str | None = None,
    icon: str | None = None,
    features: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    card: dict[str, Any] = {
        "type": "tile",
        "entity": entity_id,
    }
    if name:
        card["name"] = name
    if icon:
        card["icon"] = icon
    if features:
        card["features"] = features
    return card


def _action_button(
    *,
    name: str,
    icon: str,
    action: str,
    target_entity_id: str | None = None,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    tap_action: dict[str, Any] = {
        "action": "perform-action",
        "perform_action": action,
    }
    if target_entity_id:
        tap_action["target"] = {"entity_id": target_entity_id}
    if data:
        tap_action["data"] = data
    return {
        "type": "button",
        "name": name,
        "icon": icon,
        "tap_action": tap_action,
    }


def _navigation_button(
    *,
    name: str,
    path: str,
    dashboard_url_path: str,
    icon: str = "mdi:home-outline",
) -> dict[str, Any]:
    return {
        "type": "button",
        "name": name,
        "icon": icon,
        "tap_action": {
            "action": "navigate",
            "navigation_path": f"/{dashboard_url_path}/{path}",
        },
    }


def _unresolved_card(*, name: str, role: str) -> dict[str, Any]:
    """Keep configured objects visible even if their native binding is absent."""
    return {
        "type": "markdown",
        "content": (
            f"**{name}**  \n"
            f"Red Queen Entity nicht verfügbar (`{role}`)."
        ),
    }


def _heading(heading: str, icon: str) -> dict[str, Any]:
    return {
        "type": "heading",
        "heading": heading,
        "heading_style": "title",
        "icon": icon,
    }


def _section(
    *,
    heading: str,
    icon: str,
    cards: list[dict[str, Any]],
    column_span: int | None = None,
) -> dict[str, Any]:
    section: dict[str, Any] = {
        "type": "grid",
        "cards": [_heading(heading, icon), *cards],
    }
    if column_span is not None:
        section["column_span"] = column_span
    return section


def _global_tile(
    bindings: DashboardBindings,
    *,
    role: str,
    name: str,
    icon: str,
) -> dict[str, Any]:
    entity_id = bindings.global_entity_id(role)
    if entity_id:
        return _entity_tile(entity_id, name=name, icon=icon)
    return _unresolved_card(name=name, role=role)


def _overview_status_cards(
    model: DashboardModel,
    bindings: DashboardBindings,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = [
        _global_tile(
            bindings,
            role="house_ready",
            name="Hausstatus",
            icon="mdi:home-check",
        ),
    ]

    if model.features.openings:
        cards.append(
            _global_tile(
                bindings,
                role="openings_any_open",
                name="Öffnungen",
                icon="mdi:window-open-variant",
            )
        )

    if model.features.lights:
        cards.append(
            _global_tile(
                bindings,
                role="lighting_count_on",
                name="Licht",
                icon="mdi:lightbulb-group",
            )
        )

    if model.features.covers:
        resolved_covers = [
            item.cover.entity_id
            for item in bindings.covers
            if item.cover.entity_id
        ]
        if resolved_covers:
            cards.append(
                {
                    "type": "markdown",
                    "content": _cover_overview_template(resolved_covers),
                }
            )
        else:
            cards.append(_unresolved_card(name="Raffstores", role="covers"))

    if model.features.garage:
        garage_bindings = [
            item.garage.entity_id
            for item in bindings.openings
            if item.garage is not None and item.garage.entity_id
        ]
        if garage_bindings:
            cards.append(
                _entity_tile(
                    garage_bindings[0],
                    name=(
                        "Garagentor"
                        if len(garage_bindings) == 1
                        else "Garagentor 1"
                    ),
                    icon="mdi:garage",
                    features=[{"type": "cover-open-close"}],
                )
            )
        else:
            cards.append(_unresolved_card(name="Garage", role="garage"))

    if model.features.plants:
        care_entities = [
            item.care.entity_id
            for item in bindings.plants
            if item.care.entity_id
        ]
        if care_entities:
            cards.append(
                {
                    "type": "markdown",
                    "content": _plant_overview_template(care_entities),
                }
            )
        else:
            cards.append(_unresolved_card(name="Pflanzen", role="plant_care"))

    cards.extend(
        [
            _global_tile(
                bindings,
                role="security_secure",
                name="Sicherheit",
                icon="mdi:shield-home",
            ),
            _global_tile(
                bindings,
                role="health_score",
                name="Red Queen",
                icon="mdi:chess-queen",
            ),
        ]
    )
    return cards


def _cover_overview_template(entity_ids: list[str]) -> str:
    quoted = ", ".join(f"'{entity_id}'" for entity_id in entity_ids)
    return (
        "### Raffstores\n"
        f"{{% set ids = [{quoted}] %}}\n"
        "{% set ns = namespace(open=0, closed=0, moving=0, other=0) %}\n"
        "{% for id in ids %}\n"
        "  {% set s = states(id) %}\n"
        "  {% if s == 'open' %}{% set ns.open = ns.open + 1 %}\n"
        "  {% elif s == 'closed' %}{% set ns.closed = ns.closed + 1 %}\n"
        "  {% elif s in ['opening', 'closing'] %}"
        "{% set ns.moving = ns.moving + 1 %}\n"
        "  {% else %}{% set ns.other = ns.other + 1 %}{% endif %}\n"
        "{% endfor %}\n"
        "{{ ids | length }} gesamt · {{ ns.open }} offen · "
        "{{ ns.closed }} geschlossen"
        "{% if ns.moving > 0 %} · {{ ns.moving }} in Bewegung{% endif %}"
        "{% if ns.other > 0 %} · {{ ns.other }} prüfen{% endif %}"
    )


def _plant_overview_template(entity_ids: list[str]) -> str:
    quoted = ", ".join(f"'{entity_id}'" for entity_id in entity_ids)
    return (
        "### Pflanzen\n"
        f"{{% set ids = [{quoted}] %}}\n"
        "{% set ns = namespace(due=0, overdue=0, unknown=0, ok=0) %}\n"
        "{% for id in ids %}\n"
        "  {% set s = states(id) %}\n"
        "  {% if s == 'overdue' %}{% set ns.overdue = ns.overdue + 1 %}\n"
        "  {% elif s == 'due' %}{% set ns.due = ns.due + 1 %}\n"
        "  {% elif s == 'unknown' %}{% set ns.unknown = ns.unknown + 1 %}\n"
        "  {% else %}{% set ns.ok = ns.ok + 1 %}{% endif %}\n"
        "{% endfor %}\n"
        "{% if ns.overdue > 0 %}{{ ns.overdue }} überfällig"
        "{% if ns.due > 0 %} · {{ ns.due }} heute fällig{% endif %}\n"
        "{% elif ns.due > 0 %}{{ ns.due }} heute fällig\n"
        "{% elif ns.unknown > 0 %}{{ ns.unknown }} ohne Gießverlauf\n"
        "{% else %}alle {{ ids | length }} versorgt{% endif %}"
    )


def _overview_action_cards(
    model: DashboardModel,
    bindings: DashboardBindings,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []

    if model.features.lights:
        cards.append(
            _action_button(
                name="Licht komplett aus",
                icon="mdi:lightbulb-group-off",
                action="wnhf.lighting_all_off",
            )
        )

    for opening in model.rooms:
        for opening_spec in opening.openings:
            binding = bindings.opening_for(opening_spec.object_id)
            if binding is None:
                continue
            if opening_spec.has_door_opener:
                if binding.door_release and binding.door_release.entity_id:
                    cards.append(
                        _action_button(
                            name=f"{opening_spec.name} öffnen",
                            icon="mdi:door-open",
                            action="button.press",
                            target_entity_id=binding.door_release.entity_id,
                        )
                    )
            if opening_spec.is_garage_door:
                if binding.garage and binding.garage.entity_id:
                    cards.append(
                        _entity_tile(
                            binding.garage.entity_id,
                            name=opening_spec.name,
                            icon="mdi:garage",
                            features=[{"type": "cover-open-close"}],
                        )
                    )

    return cards


def _render_overview(
    model: DashboardModel,
    bindings: DashboardBindings,
    *,
    dashboard_url_path: str,
) -> dict[str, Any]:
    sections = [
        _section(
            heading="Haus auf einen Blick",
            icon="mdi:chess-queen",
            cards=_overview_status_cards(model, bindings),
            column_span=4,
        )
    ]

    actions = _overview_action_cards(model, bindings)
    if actions:
        sections.append(
            _section(
                heading="Hauptaktionen",
                icon="mdi:gesture-tap-button",
                cards=actions,
                column_span=4,
            )
        )

    floor_navigation = [
        _navigation_button(
            name=floor.name,
            path=floor.path,
            dashboard_url_path=dashboard_url_path,
            icon="mdi:floor-plan",
        )
        for floor in model.floors
    ]
    if floor_navigation:
        sections.append(
            _section(
                heading="Stockwerke",
                icon="mdi:home-city-outline",
                cards=floor_navigation,
                column_span=4,
            )
        )

    secondary_navigation: list[dict[str, Any]] = []
    if model.plants_path:
        secondary_navigation.append(
            _navigation_button(
                name="Pflanzen",
                path=model.plants_path,
                dashboard_url_path=dashboard_url_path,
                icon="mdi:sprout",
            )
        )
    secondary_navigation.append(
        _navigation_button(
            name="Red Queen System",
            path=model.system_path,
            dashboard_url_path=dashboard_url_path,
            icon="mdi:chess-queen",
        )
    )
    sections.append(
        _section(
            heading="Weitere Bereiche",
            icon="mdi:view-dashboard-outline",
            cards=secondary_navigation,
            column_span=4,
        )
    )

    return {
        "type": "sections",
        "title": "Übersicht",
        "path": model.overview_path,
        "icon": "mdi:chess-queen",
        "max_columns": 4,
        "header": {
            "card": {
                "type": "markdown",
                "text_only": True,
                "content": (
                    f"# Red Queen\n**{model.house_name} · Gesamtübersicht**"
                ),
            }
        },
        "sections": sections,
    }


def _room_status_markdown(
    room: DashboardRoomSpec,
    bindings: DashboardBindings,
    *,
    dashboard_url_path: str,
) -> dict[str, Any]:
    light_ids = [
        binding.light.entity_id
        for light in room.lights
        if (binding := bindings.light_for(light.object_id)) is not None
        and binding.light.entity_id
    ]
    opening_ids = [
        binding.state.entity_id
        for opening in room.openings
        if (binding := bindings.opening_for(opening.object_id)) is not None
        and binding.state.entity_id
    ]
    cover_ids = [
        binding.cover.entity_id
        for cover in room.covers
        if (binding := bindings.cover_for(cover.object_id)) is not None
        and binding.cover.entity_id
    ]
    lock_ids = [
        binding.lock.entity_id
        for opening in room.openings
        if opening.has_lock
        and (binding := bindings.opening_for(opening.object_id)) is not None
        and binding.lock is not None
        and binding.lock.entity_id
    ]

    def quoted(values: list[str]) -> str:
        return ", ".join(f"'{value}'" for value in values)

    path = f"/{dashboard_url_path}/{room.path}"
    content = (
        f"### [{room.name}]({path})\n"
        f"{{% set lights = [{quoted(light_ids)}] %}}\n"
        f"{{% set openings = [{quoted(opening_ids)}] %}}\n"
        f"{{% set covers = [{quoted(cover_ids)}] %}}\n"
        f"{{% set locks = [{quoted(lock_ids)}] %}}\n"
        "{% set lights_on = namespace(n=0) %}\n"
        "{% set openings_open = namespace(n=0) %}\n"
        "{% set unlocked = namespace(n=0) %}\n"
        "{% for id in lights %}{% if states(id) == 'on' %}"
        "{% set lights_on.n = lights_on.n + 1 %}{% endif %}{% endfor %}\n"
        "{% for id in openings %}{% if states(id) == 'on' %}"
        "{% set openings_open.n = openings_open.n + 1 %}{% endif %}{% endfor %}\n"
        "{% for id in locks %}{% if states(id) == 'unlocked' %}"
        "{% set unlocked.n = unlocked.n + 1 %}{% endif %}{% endfor %}\n"
        "{% set moving = namespace(n=0) %}\n"
        "{% set closed = namespace(n=0) %}\n"
        "{% for id in covers %}\n"
        "  {% if states(id) in ['opening', 'closing'] %}"
        "{% set moving.n = moving.n + 1 %}{% endif %}\n"
        "  {% if states(id) == 'closed' %}"
        "{% set closed.n = closed.n + 1 %}{% endif %}\n"
        "{% endfor %}\n"
        "{% set parts = [] %}\n"
        "{% if openings_open.n > 0 %}{% set parts = parts + ['🚪 ' ~ openings_open.n ~ ' offen'] %}{% endif %}\n"
        "{% if unlocked.n > 0 %}{% set parts = parts + ['🔓 ' ~ unlocked.n ~ ' entriegelt'] %}{% endif %}\n"
        "{% if lights_on.n > 0 %}{% set parts = parts + ['💡 ' ~ lights_on.n ~ ' an'] %}{% endif %}\n"
        "{% if moving.n > 0 %}{% set parts = parts + ['▤ ' ~ moving.n ~ ' fährt'] %}"
        "{% elif closed.n > 0 %}{% set parts = parts + ['▤ ' ~ closed.n ~ ' zu'] %}{% endif %}\n"
        "{{ parts | join(' · ') if parts | length > 0 else 'alles ruhig' }}"
    )
    return {"type": "markdown", "content": content}


def _render_floor(
    floor: DashboardFloorSpec,
    bindings: DashboardBindings,
    *,
    dashboard_url_path: str,
) -> dict[str, Any]:
    room_cards = [
        _room_status_markdown(
            room,
            bindings,
            dashboard_url_path=dashboard_url_path,
        )
        for room in floor.rooms
    ]
    return {
        "type": "sections",
        "title": floor.name,
        "path": floor.path,
        "icon": "mdi:floor-plan",
        "max_columns": 4,
        "header": {
            "card": {
                "type": "markdown",
                "text_only": True,
                "content": f"# {floor.name}\n**Red Queen · Räume**",
            }
        },
        "sections": [
            _section(
                heading="Räume",
                icon="mdi:floor-plan",
                cards=room_cards,
                column_span=4,
            )
        ],
    }


def _light_cards(
    room: DashboardRoomSpec,
    bindings: DashboardBindings,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for light in room.lights:
        binding = bindings.light_for(light.object_id)
        if binding is not None and binding.light.entity_id:
            cards.append(
                _entity_tile(
                    binding.light.entity_id,
                    name=light.name,
                    icon="mdi:lightbulb",
                )
            )
        else:
            cards.append(_unresolved_card(name=light.name, role="light"))
    return cards


def _opening_cards(
    room: DashboardRoomSpec,
    bindings: DashboardBindings,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for opening in room.openings:
        binding = bindings.opening_for(opening.object_id)
        if binding is None:
            cards.append(_unresolved_card(name=opening.name, role="opening"))
            continue

        if binding.state.entity_id:
            cards.append(
                _entity_tile(
                    binding.state.entity_id,
                    name=opening.name,
                    icon=_opening_icon(opening),
                )
            )
        else:
            cards.append(_unresolved_card(name=opening.name, role="opening_state"))

        if opening.is_garage_door:
            if binding.garage and binding.garage.entity_id:
                cards.append(
                    _entity_tile(
                        binding.garage.entity_id,
                        name=f"{opening.name} Steuerung",
                        icon="mdi:garage",
                        features=[{"type": "cover-open-close"}],
                    )
                )
            else:
                cards.append(_unresolved_card(name=opening.name, role="garage"))

    return cards


def _opening_icon(opening: DashboardOpeningSpec) -> str:
    return {
        "window": "mdi:window-closed-variant",
        "sliding_door": "mdi:door-sliding",
        "door": "mdi:door-closed",
        "garage_door": "mdi:garage",
    }.get(opening.opening_type, "mdi:door")


def _access_cards(
    room: DashboardRoomSpec,
    bindings: DashboardBindings,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for opening in room.openings:
        binding = bindings.opening_for(opening.object_id)
        if binding is None:
            continue

        if opening.has_lock:
            if binding.lock and binding.lock.entity_id:
                cards.extend(
                    [
                        _entity_tile(
                            binding.lock.entity_id,
                            name=f"{opening.name} Schloss",
                            icon="mdi:lock",
                        ),
                        _action_button(
                            name=f"{opening.name} verriegeln",
                            icon="mdi:lock",
                            action="lock.lock",
                            target_entity_id=binding.lock.entity_id,
                        ),
                        _action_button(
                            name=f"{opening.name} entriegeln",
                            icon="mdi:lock-open",
                            action="lock.unlock",
                            target_entity_id=binding.lock.entity_id,
                        ),
                    ]
                )
            else:
                cards.append(_unresolved_card(name=opening.name, role="lock"))

        if opening.has_door_opener:
            if binding.door_release and binding.door_release.entity_id:
                cards.append(
                    _action_button(
                        name=f"{opening.name} öffnen",
                        icon="mdi:door-open",
                        action="button.press",
                        target_entity_id=binding.door_release.entity_id,
                    )
                )
            else:
                cards.append(
                    _unresolved_card(name=opening.name, role="door_release")
                )
    return cards


def _cover_cards(
    room: DashboardRoomSpec,
    bindings: DashboardBindings,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for cover in room.covers:
        binding = bindings.cover_for(cover.object_id)
        if binding is None:
            cards.append(_unresolved_card(name=cover.name, role="cover"))
            continue

        if binding.cover.entity_id:
            cards.append(
                _entity_tile(
                    binding.cover.entity_id,
                    name=cover.name,
                    icon="mdi:window-shutter",
                    features=[{"type": "cover-open-close"}],
                )
            )
        else:
            cards.append(_unresolved_card(name=cover.name, role="cover"))

        if cover.position_feedback:
            if binding.position and binding.position.entity_id:
                cards.append(
                    _entity_tile(
                        binding.position.entity_id,
                        name=f"{cover.name} Position",
                        icon="mdi:blinds-horizontal",
                    )
                )
            else:
                cards.append(
                    _unresolved_card(name=cover.name, role="cover_position")
                )

        if cover.blade_commands:
            cards.extend(_blade_cards(cover.name, binding))
    return cards


def _blade_cards(
    cover_name: str,
    binding: DashboardCoverBinding,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    if binding.blades_open and binding.blades_open.entity_id:
        cards.append(
            _action_button(
                name=f"{cover_name} Lamellen öffnen",
                icon="mdi:blinds-open",
                action="button.press",
                target_entity_id=binding.blades_open.entity_id,
            )
        )
    else:
        cards.append(_unresolved_card(name=cover_name, role="blades_open"))

    if binding.blades_close and binding.blades_close.entity_id:
        cards.append(
            _action_button(
                name=f"{cover_name} Lamellen schließen",
                icon="mdi:blinds",
                action="button.press",
                target_entity_id=binding.blades_close.entity_id,
            )
        )
    else:
        cards.append(_unresolved_card(name=cover_name, role="blades_close"))
    return cards


def _plant_cards(
    room: DashboardRoomSpec,
    bindings: DashboardBindings,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for plant in room.plants:
        binding = bindings.plant_for(plant.object_id)
        if binding is None:
            cards.append(_unresolved_card(name=plant.name, role="plant_care"))
            continue
        cards.extend(_one_plant_cards(plant.name, binding))
    return cards


def _one_plant_cards(
    plant_name: str,
    binding: DashboardPlantBinding,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    if binding.care.entity_id:
        cards.append(
            _entity_tile(
                binding.care.entity_id,
                name=plant_name,
                icon="mdi:sprout",
            )
        )
    else:
        cards.append(_unresolved_card(name=plant_name, role="plant_care"))

    if binding.record_watering.entity_id:
        cards.append(
            _action_button(
                name=f"{plant_name} gießen protokollieren",
                icon="mdi:watering-can",
                action="button.press",
                target_entity_id=binding.record_watering.entity_id,
            )
        )
    else:
        cards.append(_unresolved_card(name=plant_name, role="record_watering"))
    return cards


def _render_room(
    room: DashboardRoomSpec,
    bindings: DashboardBindings,
) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []

    lights = _light_cards(room, bindings)
    if lights:
        sections.append(
            _section(heading="Licht", icon="mdi:lightbulb-group", cards=lights)
        )

    openings = _opening_cards(room, bindings)
    if openings:
        sections.append(
            _section(
                heading="Öffnungen",
                icon="mdi:window-open-variant",
                cards=openings,
            )
        )

    access = _access_cards(room, bindings)
    if access:
        sections.append(
            _section(heading="Zugang", icon="mdi:shield-key", cards=access)
        )

    covers = _cover_cards(room, bindings)
    if covers:
        sections.append(
            _section(
                heading="Beschattung",
                icon="mdi:window-shutter",
                cards=covers,
            )
        )

    plants = _plant_cards(room, bindings)
    if plants:
        sections.append(
            _section(heading="Pflanzen", icon="mdi:sprout", cards=plants)
        )

    if not sections:
        sections.append(
            _section(
                heading="Raum",
                icon="mdi:home-outline",
                cards=[
                    {
                        "type": "markdown",
                        "content": "Für diesen Raum sind noch keine Red Queen Objekte konfiguriert.",
                    }
                ],
            )
        )

    return {
        "type": "sections",
        "title": room.name,
        "path": room.path,
        "subview": True,
        "max_columns": 4,
        "header": {
            "card": {
                "type": "markdown",
                "text_only": True,
                "content": f"# {room.name}\n**Red Queen · Raumsteuerung**",
            }
        },
        "sections": sections,
    }


def _render_plants(
    model: DashboardModel,
    bindings: DashboardBindings,
) -> dict[str, Any]:
    cards: list[dict[str, Any]] = []
    for room in model.rooms:
        for plant in room.plants:
            binding = bindings.plant_for(plant.object_id)
            if binding is None:
                cards.append(_unresolved_card(name=plant.name, role="plant_care"))
                continue
            plant_cards = _one_plant_cards(plant.name, binding)
            if plant_cards:
                plant_cards[0]["name"] = f"{plant.name} · {room.name}"
            cards.extend(plant_cards)

    return {
        "type": "sections",
        "title": "Pflanzen",
        "path": model.plants_path,
        "icon": "mdi:sprout",
        "max_columns": 4,
        "header": {
            "card": {
                "type": "markdown",
                "text_only": True,
                "content": "# Pflanzen\n**Red Queen · Plant Care**",
            }
        },
        "sections": [
            _section(
                heading="Pflanzenpflege",
                icon="mdi:watering-can-outline",
                cards=cards,
                column_span=4,
            )
        ],
    }


def _render_system(
    model: DashboardModel,
    bindings: DashboardBindings,
) -> dict[str, Any]:
    cards = [
        _global_tile(
            bindings,
            role="framework_healthy",
            name="Framework",
            icon="mdi:heart-pulse",
        ),
        _global_tile(
            bindings,
            role="framework_version",
            name="Version",
            icon="mdi:package-variant-closed",
        ),
        _global_tile(
            bindings,
            role="health_score",
            name="Health",
            icon="mdi:heart-flash",
        ),
        _global_tile(
            bindings,
            role="registry_valid",
            name="Registry",
            icon="mdi:database-check",
        ),
        _global_tile(
            bindings,
            role="registry_validation_status",
            name="Validation",
            icon="mdi:check-decagram-outline",
        ),
        _global_tile(
            bindings,
            role="registry_validation_issues",
            name="Validation Details",
            icon="mdi:alert-circle-outline",
        ),
        _global_tile(
            bindings,
            role="access_all_available",
            name="Access verfügbar",
            icon="mdi:access-point-check",
        ),
        _global_tile(
            bindings,
            role="access_attention_required",
            name="Access Aufmerksamkeit",
            icon="mdi:shield-alert-outline",
        ),
    ]

    if bindings.issues:
        issue_lines = "\n".join(
            f"- `{issue.object_id}` · {issue.role} · `{issue.unique_id}`"
            for issue in bindings.issues
        )
        cards.append(
            {
                "type": "markdown",
                "content": (
                    "### Nicht aufgelöste native Entities\n"
                    f"{issue_lines}"
                ),
            }
        )

    return {
        "type": "sections",
        "title": "Red Queen",
        "path": model.system_path,
        "icon": "mdi:chess-queen",
        "max_columns": 4,
        "header": {
            "card": {
                "type": "markdown",
                "text_only": True,
                "content": "# Red Queen\n**System & Diagnose**",
            }
        },
        "sections": [
            _section(
                heading="System",
                icon="mdi:shield-home",
                cards=cards,
                column_span=4,
            )
        ],
    }


def _canonical_sha256(config: dict[str, Any]) -> str:
    encoded = json.dumps(
        config,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def render_dashboard(
    model: DashboardModel,
    bindings: DashboardBindings,
    *,
    dashboard_url_path: str = DEFAULT_DASHBOARD_URL_PATH,
    title: str = "Red Queen",
) -> DashboardRenderResult:
    """Render a complete native Lovelace dashboard configuration.

    The same model and bindings produce the same logical configuration and the
    same ``config_sha256``.  Unresolved expected native entities remain visible
    as native Markdown diagnostic cards rather than being silently omitted.
    """
    url_path = dashboard_url_path.strip("/")
    if not url_path:
        raise ValueError("dashboard_url_path must not be empty")

    views: list[dict[str, Any]] = [
        _render_overview(
            model,
            bindings,
            dashboard_url_path=url_path,
        )
    ]

    for floor in model.floors:
        views.append(
            _render_floor(
                floor,
                bindings,
                dashboard_url_path=url_path,
            )
        )

    for room in model.rooms:
        views.append(_render_room(room, bindings))

    if model.plants_path:
        views.append(_render_plants(model, bindings))

    views.append(_render_system(model, bindings))

    config: dict[str, Any] = {
        "title": title,
        "views": views,
    }
    digest = _canonical_sha256(config)
    metadata = DashboardRenderMetadata(
        renderer_contract_version=DASHBOARD_RENDERER_CONTRACT_VERSION,
        model_contract_version=model.contract_version,
        binding_contract_version=bindings.contract_version,
        config_sha256=digest,
        view_count=len(views),
        floor_view_count=len(model.floors),
        room_view_count=len(model.rooms),
        unresolved_binding_count=len(bindings.issues),
    )
    return DashboardRenderResult(config=config, metadata=metadata)
