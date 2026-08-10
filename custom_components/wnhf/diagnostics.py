"""Diagnostics model for WNHF."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ModuleDiagnostic:
    """Runtime information about one WNHF module."""

    module_id: str
    version: str
    status: str
    objects: int
    services: tuple[str, ...]
    entities: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a Home Assistant attribute-safe dictionary."""
        return {
            "module_id": self.module_id,
            "version": self.version,
            "status": self.status,
            "objects": self.objects,
            "services": list(self.services),
            "entities": list(self.entities),
        }


@dataclass(frozen=True, slots=True)
class DiagnosticsSnapshot:
    """Immutable diagnostics snapshot."""

    framework_version: str
    runtime_status: str
    health_status: str
    health_score: int
    registry_status: str
    registry_loaded_at: datetime | None
    registry_load_ms: float | None
    house_id: str | None
    house_name: str | None
    room_count: int
    light_count: int
    opening_count: int
    cover_count: int
    enabled_light_count: int
    controllable_light_count: int
    warning_count: int
    warnings: tuple[str, ...]
    capabilities: dict[str, bool]
    modules: dict[str, ModuleDiagnostic]

    def module_attributes(self) -> dict[str, Any]:
        """Return all module diagnostics as nested dictionaries."""
        return {
            module_id: module.as_dict()
            for module_id, module in self.modules.items()
        }
