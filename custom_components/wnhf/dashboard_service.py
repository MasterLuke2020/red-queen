"""Orchestrate Red Queen dashboard generation without hiding side effects.

The RC12 dashboard stack is deliberately split into small contracts:

    House -> DashboardModel -> DashboardBindings -> DashboardRenderResult
                                             -> DashboardAdapter

This module composes those contracts for Home Assistant.  Preparing or checking
status is read-only.  Persisting Lovelace configuration happens only through an
explicit ``async_apply`` call and remains delegated to ``dashboard_adapter``.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import floor_registry as fr
from homeassistant.util import slugify

from .const import DATA_ENGINE, DOMAIN
from .dashboard_adapter import (
    DASHBOARD_RUNTIME_KEY,
    DashboardAdapterError,
    DashboardApplyResult,
    DashboardLifecycleStatus,
    RedQueenDashboardAdapter,
)
from .dashboard_binding import DashboardBindings, resolve_dashboard_bindings
from .dashboard_model import (
    DashboardFloorDescriptor,
    DashboardModel,
    build_dashboard_model,
)
from .dashboard_renderer import DashboardRenderResult, render_dashboard
from .engine import WNHFEngine


DASHBOARD_GENERATION_CONTRACT_VERSION = "1.0"
DASHBOARD_SERVICE_RUNTIME_KEY = "dashboard_generation_service"

# Only semantic registry files that can influence the generated dashboard are
# part of the source digest.  Notifications and other future registries are not
# included until they become part of the dashboard contract.
_DASHBOARD_REGISTRY_FILES = (
    "rooms.yaml",
    "lights.yaml",
    "covers.yaml",
    "openings.yaml",
    "plants.yaml",
)


class DashboardGenerationError(Exception):
    """Raised when the dashboard generation pipeline cannot be prepared safely."""


@dataclass(frozen=True, slots=True)
class DashboardGenerationPreview:
    """One complete, read-only compilation of the current Red Queen house."""

    contract_version: str
    model: DashboardModel
    bindings: DashboardBindings
    rendered: DashboardRenderResult
    source_registry_sha256: str

    def as_dict(self) -> dict[str, Any]:
        """Return compact metadata without embedding the Lovelace configuration."""
        return {
            "contract_version": self.contract_version,
            "source_registry_sha256": self.source_registry_sha256,
            "binding_complete": self.bindings.complete,
            "binding_expected_entities": self.bindings.expected_entity_count,
            "binding_resolved_entities": self.bindings.resolved_entity_count,
            "binding_issue_count": len(self.bindings.issues),
            "counts": {
                "floors": self.model.counts.floors,
                "rooms": self.model.counts.rooms,
                "lights": self.model.counts.lights,
                "covers": self.model.counts.covers,
                "openings": self.model.counts.openings,
                "garages": self.model.counts.garages,
                "plants": self.model.counts.plants,
            },
            "render": self.rendered.metadata.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class DashboardGenerationStatus:
    """Current generated expectation together with persisted lifecycle state."""

    preview: DashboardGenerationPreview
    lifecycle: DashboardLifecycleStatus

    def as_dict(self) -> dict[str, Any]:
        """Return serializable Configurator/status information."""
        return {
            **self.preview.as_dict(),
            "lifecycle": self.lifecycle.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class DashboardGenerationApplyResult:
    """Result of one explicit Red Queen dashboard create/update operation."""

    preview: DashboardGenerationPreview
    applied: DashboardApplyResult

    def as_dict(self) -> dict[str, Any]:
        """Return serializable result metadata."""
        return {
            **self.preview.as_dict(),
            "apply": self.applied.as_dict(),
        }


def _semantic_floor_key(name: str) -> str:
    """Mirror the configurator's stable semantic floor segment."""
    return slugify(name) or "unassigned"


def _floor_descriptors(
    hass: HomeAssistant,
    house_floor_ids: set[str],
) -> tuple[DashboardFloorDescriptor, ...]:
    """Resolve Home Assistant Floor Registry metadata for known semantic floors.

    Managed RC11 rooms use a slug of the Home Assistant floor name as their
    semantic ``floor`` value.  Manual registries may instead use the actual HA
    floor id.  Supporting both keys keeps generated and installation-owned
    registries deterministic without guessing from room names.
    """
    registry = fr.async_get(hass)
    descriptors: dict[str, DashboardFloorDescriptor] = {}

    floors = sorted(
        registry.async_list_floors(),
        key=lambda item: (item.name.casefold(), item.floor_id),
    )
    for floor in floors:
        order = floor.level if isinstance(floor.level, int) else None
        descriptor_keys = (floor.floor_id, _semantic_floor_key(floor.name))
        for floor_id in descriptor_keys:
            if floor_id not in house_floor_ids or floor_id in descriptors:
                continue
            descriptors[floor_id] = DashboardFloorDescriptor(
                floor_id=floor_id,
                name=floor.name,
                order=order,
            )

    return tuple(
        descriptors[floor_id]
        for floor_id in sorted(descriptors)
    )


def _registry_source_sha256(registry_dir: Path) -> str:
    """Hash the dashboard-relevant registry source deterministically.

    Line endings are normalized so Windows working-copy behavior never changes
    the logical source revision.  A missing optional file is represented by a
    stable marker instead of being silently ignored.
    """
    digest = sha256()
    for filename in _DASHBOARD_REGISTRY_FILES:
        path = registry_dir / filename
        digest.update(filename.encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            content = path.read_bytes().replace(b"\r\n", b"\n")
            digest.update(content)
        else:
            digest.update(b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()


class RedQueenDashboardGenerationService:
    """Compile and explicitly apply the current Red Queen dashboard."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    def _engine(self) -> WNHFEngine:
        domain_data = self.hass.data.get(DOMAIN, {})
        engine = domain_data.get(DATA_ENGINE)
        if not isinstance(engine, WNHFEngine):
            raise DashboardGenerationError(
                "Red Queen runtime engine is not available."
            )
        if engine.safe_mode:
            raise DashboardGenerationError(
                "Dashboard generation is disabled while Red Queen is in "
                "registry recovery mode."
            )
        return engine

    def _adapter(self) -> RedQueenDashboardAdapter:
        domain_data = self.hass.data.get(DOMAIN, {})
        adapter = domain_data.get(DASHBOARD_RUNTIME_KEY)
        if not isinstance(adapter, RedQueenDashboardAdapter):
            raise DashboardGenerationError(
                "Red Queen dashboard adapter is not available."
            )
        return adapter

    async def async_preview(self) -> DashboardGenerationPreview:
        """Compile the current dashboard completely without persisting it."""
        engine = self._engine()
        house = engine._require_house()
        house_floor_ids = {
            room.floor_id
            for room in house.rooms.values()
            if room.enabled
        }
        descriptors = _floor_descriptors(self.hass, house_floor_ids)
        model = build_dashboard_model(
            house,
            floor_descriptors=descriptors,
        )
        bindings = resolve_dashboard_bindings(self.hass, model)
        rendered = render_dashboard(model, bindings)
        source_sha = await self.hass.async_add_executor_job(
            _registry_source_sha256,
            engine.registry_dir,
        )
        return DashboardGenerationPreview(
            contract_version=DASHBOARD_GENERATION_CONTRACT_VERSION,
            model=model,
            bindings=bindings,
            rendered=rendered,
            source_registry_sha256=source_sha,
        )

    async def async_status(self) -> DashboardGenerationStatus:
        """Compare the current expected render with persisted dashboard state."""
        preview = await self.async_preview()
        try:
            lifecycle = await self._adapter().async_status(
                expected_render=preview.rendered,
            )
        except DashboardAdapterError as err:
            raise DashboardGenerationError(str(err)) from err
        return DashboardGenerationStatus(
            preview=preview,
            lifecycle=lifecycle,
        )

    async def async_apply(self) -> DashboardGenerationApplyResult:
        """Explicitly create or update the Red Queen managed dashboard."""
        preview = await self.async_preview()
        try:
            applied = await self._adapter().async_apply(
                preview.rendered,
                source_registry_sha256=preview.source_registry_sha256,
            )
        except DashboardAdapterError as err:
            raise DashboardGenerationError(str(err)) from err
        return DashboardGenerationApplyResult(
            preview=preview,
            applied=applied,
        )


async def async_setup_dashboard_generation_service(
    hass: HomeAssistant,
) -> RedQueenDashboardGenerationService:
    """Expose the generation service without generating or writing anything."""
    service = RedQueenDashboardGenerationService(hass)
    hass.data.setdefault(DOMAIN, {})[DASHBOARD_SERVICE_RUNTIME_KEY] = service
    return service


async def async_unload_dashboard_generation_service(hass: HomeAssistant) -> None:
    """Remove the runtime generation facade; persisted dashboard stays intact."""
    hass.data.get(DOMAIN, {}).pop(DASHBOARD_SERVICE_RUNTIME_KEY, None)


def dashboard_generation_service(
    hass: HomeAssistant,
) -> RedQueenDashboardGenerationService:
    """Return the active generation service for Configurator/API consumers."""
    service = hass.data.get(DOMAIN, {}).get(DASHBOARD_SERVICE_RUNTIME_KEY)
    if not isinstance(service, RedQueenDashboardGenerationService):
        raise DashboardGenerationError(
            "Red Queen dashboard generation service is not initialized."
        )
    return service
