"""Public read-only manager for the semantic capability layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .registry import CapabilityRegistry
from .resolver import CapabilityResolver


class CapabilityManager:
    """Single public read-only entry point for capability consumers."""

    API_VERSION = "1.0"
    VERSION = "1.0-stage4.6.3"

    def __init__(
        self,
        registry: CapabilityRegistry,
        resolver: CapabilityResolver,
    ) -> None:
        self._registry = registry
        self._resolver = resolver

    async def async_status(self) -> dict[str, Any]:
        """Return aggregate capability-layer status."""
        resolver_snapshot = self._resolver.snapshot()
        summary = resolver_snapshot["summary"]

        return {
            "api_version": self.API_VERSION,
            "manager_version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "read_only": True,
            "execution_enabled": False,
            "summary": {
                "registered": len(
                    self._registry.capability_ids()
                ),
                "resolved": summary["resolved"],
                "available": summary["available"],
                "healthy": summary["healthy"],
                "unresolved": summary["unresolved"],
                "all_resolved": summary["all_resolved"],
                "all_available": summary["all_available"],
                "all_healthy": summary["all_healthy"],
            },
            "registry_revision": self._registry.revision,
            "capability_ids": list(
                self._registry.capability_ids()
            ),
        }

    async def async_get_capabilities(self) -> dict[str, Any]:
        """Return a compact list of all semantic capabilities."""
        items: list[dict[str, Any]] = []

        for definition in self._registry.definitions():
            resolution = self._resolver.resolve(
                definition.capability_id
            )
            items.append({
                "capability_id": definition.capability_id,
                "version": definition.version,
                "name": definition.name,
                "kind": definition.kind.value,
                "enabled": definition.enabled,
                "actions": [
                    action.action_id
                    for action in definition.actions
                ],
                "status": resolution.status.value,
                "resolved": resolution.resolved,
                "available": resolution.available,
                "healthy": resolution.healthy,
                "selected_provider_ids": list(
                    resolution.selected_provider_ids
                ),
            })

        return {
            "api_version": self.API_VERSION,
            "manager_version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "read_only": True,
            "count": len(items),
            "capabilities": items,
        }

    async def async_get_capability(
        self,
        capability_id: str,
    ) -> dict[str, Any]:
        """Return one complete capability description."""
        definition = self._registry.get(capability_id)
        resolution = self._resolver.resolve(capability_id)

        if definition is None:
            return {
                "api_version": self.API_VERSION,
                "manager_version": self.VERSION,
                "generated_at": datetime.now(UTC).isoformat(),
                "read_only": True,
                "found": False,
                "capability_id": capability_id,
                "definition": None,
                "resolution": resolution.as_dict(),
                "diagnostics": {
                    "status": "error",
                    "warnings": [],
                    "errors": [
                        "Capability is not registered."
                    ],
                },
            }

        warnings: list[str] = []
        errors: list[str] = []

        if not definition.enabled:
            warnings.append(
                "Capability is intentionally disabled."
            )
        if not resolution.resolved:
            errors.append(
                "Capability provider bindings are unresolved."
            )
        elif not resolution.available:
            warnings.append(
                "Capability is resolved but unavailable."
            )
        elif not resolution.healthy:
            warnings.append(
                "Capability is available but degraded."
            )

        return {
            "api_version": self.API_VERSION,
            "manager_version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "read_only": True,
            "found": True,
            "capability_id": capability_id,
            "definition": definition.as_dict(),
            "resolution": resolution.as_dict(),
            "diagnostics": {
                "status": (
                    "error"
                    if errors
                    else "warning"
                    if warnings
                    else "healthy"
                ),
                "warnings": warnings,
                "errors": errors,
            },
        }
