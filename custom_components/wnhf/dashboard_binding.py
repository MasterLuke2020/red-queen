"""Native Home Assistant entity binding for the Red Queen dashboard.

The dashboard model is intentionally platform-neutral.  This module is the
single bridge from stable Red Queen semantic object IDs to the *current* Home
Assistant entity IDs registered for the native Red Queen entities.

Bindings are resolved exclusively through Home Assistant's Entity Registry and
stable Red Queen ``unique_id`` values.  The implementation never scans runtime
states and never binds provider entities such as PLC/OPC-UA/MQTT entities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .dashboard_model import DashboardModel


DASHBOARD_BINDING_CONTRACT_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class DashboardEntityRef:
    """One expected native Red Queen entity and its current HA entity ID."""

    domain: str
    unique_id: str
    entity_id: str | None

    @property
    def resolved(self) -> bool:
        """Return whether Home Assistant currently has the entity registered."""
        return self.entity_id is not None


@dataclass(frozen=True, slots=True)
class DashboardBindingIssue:
    """Describe one expected native entity that could not be resolved."""

    object_id: str
    role: str
    domain: str
    unique_id: str


@dataclass(frozen=True, slots=True)
class DashboardGlobalBinding:
    """One stable framework/house entity used by overview or diagnostics."""

    role: str
    entity: DashboardEntityRef


@dataclass(frozen=True, slots=True)
class DashboardLightBinding:
    """Native entity binding for one semantic light."""

    object_id: str
    light: DashboardEntityRef


@dataclass(frozen=True, slots=True)
class DashboardCoverBinding:
    """Native entity bindings for one semantic venetian blind."""

    object_id: str
    cover: DashboardEntityRef
    position: DashboardEntityRef | None
    blades_open: DashboardEntityRef | None
    blades_close: DashboardEntityRef | None


@dataclass(frozen=True, slots=True)
class DashboardOpeningBinding:
    """Native entity bindings for one semantic opening/access object."""

    object_id: str
    state: DashboardEntityRef
    garage: DashboardEntityRef | None
    lock: DashboardEntityRef | None
    door_release: DashboardEntityRef | None


@dataclass(frozen=True, slots=True)
class DashboardPlantBinding:
    """Native entity bindings for one semantic Plant Care object."""

    object_id: str
    care: DashboardEntityRef
    record_watering: DashboardEntityRef


@dataclass(frozen=True, slots=True)
class DashboardBindings:
    """Complete deterministic native-entity binding result for one dashboard."""

    contract_version: str
    globals: tuple[DashboardGlobalBinding, ...]
    lights: tuple[DashboardLightBinding, ...]
    covers: tuple[DashboardCoverBinding, ...]
    openings: tuple[DashboardOpeningBinding, ...]
    plants: tuple[DashboardPlantBinding, ...]
    issues: tuple[DashboardBindingIssue, ...]

    @property
    def complete(self) -> bool:
        """Return whether every expected Red Queen entity could be resolved."""
        return not self.issues

    @property
    def expected_entity_count(self) -> int:
        """Return the number of native entities expected by this binding."""
        refs: list[DashboardEntityRef] = [
            item.entity for item in self.globals
        ]
        refs.extend(item.light for item in self.lights)
        for item in self.covers:
            refs.append(item.cover)
            refs.extend(
                ref
                for ref in (item.position, item.blades_open, item.blades_close)
                if ref is not None
            )
        for item in self.openings:
            refs.append(item.state)
            refs.extend(
                ref
                for ref in (item.garage, item.lock, item.door_release)
                if ref is not None
            )
        for item in self.plants:
            refs.extend((item.care, item.record_watering))
        return len(refs)

    @property
    def resolved_entity_count(self) -> int:
        """Return how many expected native entities were resolved."""
        return self.expected_entity_count - len(self.issues)

    def global_entity_id(self, role: str) -> str | None:
        """Return one resolved global entity ID by stable dashboard role."""
        for item in self.globals:
            if item.role == role:
                return item.entity.entity_id
        return None

    def light_for(self, object_id: str) -> DashboardLightBinding | None:
        """Return bindings for one semantic light."""
        return next((item for item in self.lights if item.object_id == object_id), None)

    def cover_for(self, object_id: str) -> DashboardCoverBinding | None:
        """Return bindings for one semantic cover."""
        return next((item for item in self.covers if item.object_id == object_id), None)

    def opening_for(self, object_id: str) -> DashboardOpeningBinding | None:
        """Return bindings for one semantic opening."""
        return next((item for item in self.openings if item.object_id == object_id), None)

    def plant_for(self, object_id: str) -> DashboardPlantBinding | None:
        """Return bindings for one semantic plant."""
        return next((item for item in self.plants if item.object_id == object_id), None)


def _object_slug(object_id: str, prefix: str) -> str:
    """Reproduce the stable RC11 native-entity unique-id object segment."""
    return object_id.removeprefix(prefix).replace(".", "_")


def _light_unique_id(object_id: str) -> str:
    return f"wnhf_{_object_slug(object_id, 'light.')}"


def _cover_unique_id(object_id: str) -> str:
    return f"wnhf_{_object_slug(object_id, 'cover.')}"


def _cover_position_unique_id(object_id: str) -> str:
    return f"wnhf_cover_position_{_object_slug(object_id, 'cover.')}"


def _cover_blade_unique_id(object_id: str, direction: str) -> str:
    return f"wnhf_blades_{direction}_{_object_slug(object_id, 'cover.')}"


def _opening_unique_id(object_id: str) -> str:
    return f"wnhf_opening_{_object_slug(object_id, 'opening.')}"


def _garage_unique_id(object_id: str) -> str:
    return f"wnhf_garage_{_object_slug(object_id, 'opening.')}"


def _lock_unique_id(object_id: str) -> str:
    return f"wnhf_lock_{_object_slug(object_id, 'opening.')}"


def _door_release_unique_id(object_id: str) -> str:
    return f"wnhf_door_release_{_object_slug(object_id, 'opening.')}"


def _plant_care_unique_id(object_id: str) -> str:
    return f"wnhf_plant_care_{_object_slug(object_id, 'plant.')}"


def _plant_water_unique_id(object_id: str) -> str:
    return f"wnhf_plant_water_{_object_slug(object_id, 'plant.')}"


_GLOBAL_ENTITY_CONTRACT: tuple[tuple[str, str, str], ...] = (
    ("house_ready", "binary_sensor", "wnhf_house_ready"),
    ("framework_healthy", "binary_sensor", "wnhf_framework_healthy"),
    ("registry_valid", "binary_sensor", "wnhf_registry_valid"),
    ("security_secure", "binary_sensor", "wnhf_security_secure"),
    ("access_all_available", "binary_sensor", "wnhf_access_all_available"),
    (
        "access_attention_required",
        "binary_sensor",
        "wnhf_access_attention_required",
    ),
    ("openings_any_open", "binary_sensor", "wnhf_openings_any_open"),
    ("lighting_any_on", "binary_sensor", "wnhf_lighting_any_on"),
    ("lighting_count_on", "sensor", "wnhf_lighting_count_on"),
    ("openings_count_open", "sensor", "wnhf_openings_count_open"),
    ("framework_version", "sensor", "wnhf_framework_version"),
    ("health_score", "sensor", "wnhf_health_score"),
    (
        "registry_validation_status",
        "sensor",
        "wnhf_registry_validation_status",
    ),
    (
        "registry_validation_issues",
        "sensor",
        "wnhf_registry_validation_issues",
    ),
)


def _resolve(
    registry: er.EntityRegistry,
    *,
    domain: str,
    unique_id: str,
) -> DashboardEntityRef:
    """Resolve a native Red Queen unique ID to its current HA entity ID."""
    return DashboardEntityRef(
        domain=domain,
        unique_id=unique_id,
        entity_id=registry.async_get_entity_id(domain, DOMAIN, unique_id),
    )


def _issue_if_unresolved(
    issues: list[DashboardBindingIssue],
    *,
    object_id: str,
    role: str,
    ref: DashboardEntityRef | None,
) -> None:
    if ref is None or ref.resolved:
        return
    issues.append(
        DashboardBindingIssue(
            object_id=object_id,
            role=role,
            domain=ref.domain,
            unique_id=ref.unique_id,
        )
    )


def _check_refs(
    issues: list[DashboardBindingIssue],
    *,
    object_id: str,
    refs: Iterable[tuple[str, DashboardEntityRef | None]],
) -> None:
    for role, ref in refs:
        _issue_if_unresolved(
            issues,
            object_id=object_id,
            role=role,
            ref=ref,
        )


def resolve_dashboard_bindings(
    hass: HomeAssistant,
    model: DashboardModel,
) -> DashboardBindings:
    """Resolve every native entity expected by a ``DashboardModel``.

    Resolution uses stable integration ``unique_id`` contracts via Home
    Assistant's Entity Registry.  Therefore user-renamed entity IDs are picked
    up automatically on the next dashboard refresh.

    The function is intentionally side-effect free: it does not create, rename,
    enable or disable entities and it does not inspect provider entities.
    """
    registry = er.async_get(hass)
    issues: list[DashboardBindingIssue] = []

    globals_: list[DashboardGlobalBinding] = []
    for role, domain, unique_id in _GLOBAL_ENTITY_CONTRACT:
        ref = _resolve(registry, domain=domain, unique_id=unique_id)
        globals_.append(DashboardGlobalBinding(role=role, entity=ref))
        _issue_if_unresolved(
            issues,
            object_id=model.house_id,
            role=role,
            ref=ref,
        )

    lights: list[DashboardLightBinding] = []
    covers: list[DashboardCoverBinding] = []
    openings: list[DashboardOpeningBinding] = []
    plants: list[DashboardPlantBinding] = []

    for room in model.rooms:
        for light in room.lights:
            ref = _resolve(
                registry,
                domain="light",
                unique_id=_light_unique_id(light.object_id),
            )
            lights.append(
                DashboardLightBinding(
                    object_id=light.object_id,
                    light=ref,
                )
            )
            _issue_if_unresolved(
                issues,
                object_id=light.object_id,
                role="light",
                ref=ref,
            )

        for cover in room.covers:
            cover_ref = _resolve(
                registry,
                domain="cover",
                unique_id=_cover_unique_id(cover.object_id),
            )
            position_ref = (
                _resolve(
                    registry,
                    domain="sensor",
                    unique_id=_cover_position_unique_id(cover.object_id),
                )
                if cover.position_feedback
                else None
            )
            blades_open_ref = (
                _resolve(
                    registry,
                    domain="button",
                    unique_id=_cover_blade_unique_id(cover.object_id, "open"),
                )
                if cover.blade_commands
                else None
            )
            blades_close_ref = (
                _resolve(
                    registry,
                    domain="button",
                    unique_id=_cover_blade_unique_id(cover.object_id, "close"),
                )
                if cover.blade_commands
                else None
            )
            covers.append(
                DashboardCoverBinding(
                    object_id=cover.object_id,
                    cover=cover_ref,
                    position=position_ref,
                    blades_open=blades_open_ref,
                    blades_close=blades_close_ref,
                )
            )
            _check_refs(
                issues,
                object_id=cover.object_id,
                refs=(
                    ("cover", cover_ref),
                    ("cover_position", position_ref),
                    ("blades_open", blades_open_ref),
                    ("blades_close", blades_close_ref),
                ),
            )

        for opening in room.openings:
            state_ref = _resolve(
                registry,
                domain="binary_sensor",
                unique_id=_opening_unique_id(opening.object_id),
            )
            garage_ref = (
                _resolve(
                    registry,
                    domain="cover",
                    unique_id=_garage_unique_id(opening.object_id),
                )
                if opening.is_garage_door
                else None
            )
            lock_ref = (
                _resolve(
                    registry,
                    domain="lock",
                    unique_id=_lock_unique_id(opening.object_id),
                )
                if opening.has_lock
                else None
            )
            release_ref = (
                _resolve(
                    registry,
                    domain="button",
                    unique_id=_door_release_unique_id(opening.object_id),
                )
                if opening.has_door_opener
                else None
            )
            openings.append(
                DashboardOpeningBinding(
                    object_id=opening.object_id,
                    state=state_ref,
                    garage=garage_ref,
                    lock=lock_ref,
                    door_release=release_ref,
                )
            )
            _check_refs(
                issues,
                object_id=opening.object_id,
                refs=(
                    ("opening_state", state_ref),
                    ("garage", garage_ref),
                    ("lock", lock_ref),
                    ("door_release", release_ref),
                ),
            )

        for plant in room.plants:
            care_ref = _resolve(
                registry,
                domain="sensor",
                unique_id=_plant_care_unique_id(plant.object_id),
            )
            watering_ref = _resolve(
                registry,
                domain="button",
                unique_id=_plant_water_unique_id(plant.object_id),
            )
            plants.append(
                DashboardPlantBinding(
                    object_id=plant.object_id,
                    care=care_ref,
                    record_watering=watering_ref,
                )
            )
            _check_refs(
                issues,
                object_id=plant.object_id,
                refs=(
                    ("plant_care", care_ref),
                    ("record_watering", watering_ref),
                ),
            )

    return DashboardBindings(
        contract_version=DASHBOARD_BINDING_CONTRACT_VERSION,
        globals=tuple(globals_),
        lights=tuple(lights),
        covers=tuple(covers),
        openings=tuple(openings),
        plants=tuple(plants),
        issues=tuple(issues),
    )
