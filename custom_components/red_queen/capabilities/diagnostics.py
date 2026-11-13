"""Capability-layer diagnostics facade."""

from __future__ import annotations

from typing import Any

from .base import capability_contract_definition
from .registry import CapabilityRegistry
from .resolver import CapabilityResolver


class CapabilityDiagnostics:
    """Expose capability contract and registry diagnostics."""

    VERSION = "1.0-stage4.6.1"

    def __init__(
        self,
        registry: CapabilityRegistry,
        provider_registry: Any,
        resolver: CapabilityResolver | None = None,
    ) -> None:
        self._registry = registry
        self._provider_registry = provider_registry
        self._resolver = resolver

    def snapshot(self) -> dict[str, Any]:
        """Return the complete read-only capability diagnostics."""
        registry_snapshot = self._registry.diagnostics(
            provider_registry=self._provider_registry,
        )
        return {
            "api_version": "1.0",
            "diagnostics_version": self.VERSION,
            "contract": capability_contract_definition(),
            "registry": registry_snapshot,
            "resolver": (
                self._resolver.snapshot()
                if self._resolver is not None
                else None
            ),
        }
