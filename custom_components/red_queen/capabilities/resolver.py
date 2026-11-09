"""Explainable semantic capability resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from .base import CapabilityDefinition
from .registry import CapabilityRegistry


class CapabilityResolutionStatus(StrEnum):
    """Stable public resolution state."""

    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    DISABLED = "disabled"
    PROVIDER_UNRESOLVED = "provider_unresolved"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_UNHEALTHY = "provider_unhealthy"


@dataclass(frozen=True, slots=True)
class ProviderBindingResolution:
    """One required provider-capability binding."""

    provider_capability_id: str
    resolved: bool
    selected_provider_id: str | None
    candidate_provider_ids: tuple[str, ...]
    loaded: bool | None
    available: bool | None
    healthy: bool | None
    priority: int | None
    reason: str

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable binding result."""
        return {
            "provider_capability_id": self.provider_capability_id,
            "resolved": self.resolved,
            "selected_provider_id": self.selected_provider_id,
            "candidate_provider_ids": list(
                self.candidate_provider_ids
            ),
            "runtime": {
                "loaded": self.loaded,
                "available": self.available,
                "healthy": self.healthy,
            },
            "priority": self.priority,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class CapabilityResolution:
    """Complete semantic capability resolution."""

    capability_id: str
    status: CapabilityResolutionStatus
    resolved: bool
    available: bool
    healthy: bool
    definition: dict[str, Any] | None
    provider_bindings: tuple[ProviderBindingResolution, ...]
    selected_provider_ids: tuple[str, ...]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        """Return the public resolution contract."""
        return {
            "capability_id": self.capability_id,
            "status": self.status.value,
            "resolved": self.resolved,
            "available": self.available,
            "healthy": self.healthy,
            "definition": self.definition,
            "provider_bindings": [
                item.as_dict()
                for item in self.provider_bindings
            ],
            "selected_provider_ids": list(
                self.selected_provider_ids
            ),
            "reason": self.reason,
        }


class CapabilityResolver:
    """Resolve semantic capability definitions to runtime providers."""

    VERSION = "1.0-stage4.6.2"

    def __init__(
        self,
        capability_registry: CapabilityRegistry,
        provider_registry: Any,
    ) -> None:
        self._capability_registry = capability_registry
        self._provider_registry = provider_registry

    def resolve(
        self,
        capability_id: str,
    ) -> CapabilityResolution:
        """Resolve one semantic capability without executing anything."""
        definition = self._capability_registry.get(capability_id)

        if definition is None:
            return CapabilityResolution(
                capability_id=capability_id,
                status=CapabilityResolutionStatus.NOT_FOUND,
                resolved=False,
                available=False,
                healthy=False,
                definition=None,
                provider_bindings=(),
                selected_provider_ids=(),
                reason=(
                    "No semantic capability definition is registered."
                ),
            )

        if not definition.enabled:
            return CapabilityResolution(
                capability_id=capability_id,
                status=CapabilityResolutionStatus.DISABLED,
                resolved=False,
                available=False,
                healthy=False,
                definition=definition.as_dict(),
                provider_bindings=(),
                selected_provider_ids=(),
                reason="Capability is intentionally disabled.",
            )

        bindings = tuple(
            self._resolve_provider_binding(
                provider_capability_id
            )
            for provider_capability_id in (
                definition.required_provider_capabilities
            )
        )

        unresolved = [
            binding for binding in bindings
            if not binding.resolved
        ]
        unavailable = [
            binding for binding in bindings
            if binding.resolved and not bool(binding.available)
        ]
        unhealthy = [
            binding for binding in bindings
            if binding.resolved and not bool(binding.healthy)
        ]

        if unresolved:
            status = (
                CapabilityResolutionStatus.PROVIDER_UNRESOLVED
            )
            reason = (
                "At least one required provider capability could not "
                "be resolved."
            )
        elif unavailable:
            status = (
                CapabilityResolutionStatus.PROVIDER_UNAVAILABLE
            )
            reason = (
                "All provider bindings resolved, but at least one "
                "selected provider is unavailable."
            )
        elif unhealthy:
            status = (
                CapabilityResolutionStatus.PROVIDER_UNHEALTHY
            )
            reason = (
                "All provider bindings resolved and are available, but "
                "at least one selected provider is unhealthy."
            )
        else:
            status = CapabilityResolutionStatus.RESOLVED
            reason = (
                "Capability definition and all required provider "
                "bindings resolved to loaded, available and healthy "
                "providers."
            )

        resolved = not unresolved
        available = resolved and not unavailable
        healthy = available and not unhealthy

        return CapabilityResolution(
            capability_id=capability_id,
            status=status,
            resolved=resolved,
            available=available,
            healthy=healthy,
            definition=definition.as_dict(),
            provider_bindings=bindings,
            selected_provider_ids=tuple(
                binding.selected_provider_id
                for binding in bindings
                if binding.selected_provider_id is not None
            ),
            reason=reason,
        )

    def resolve_action(
        self,
        action_id: str,
    ) -> CapabilityResolution:
        """Resolve a declared semantic action to its parent capability."""
        matches: list[CapabilityDefinition] = []

        for definition in self._capability_registry.definitions():
            if any(
                action.action_id == action_id
                for action in definition.actions
            ):
                matches.append(definition)

        if not matches:
            return CapabilityResolution(
                capability_id=action_id,
                status=CapabilityResolutionStatus.NOT_FOUND,
                resolved=False,
                available=False,
                healthy=False,
                definition=None,
                provider_bindings=(),
                selected_provider_ids=(),
                reason=(
                    "No registered capability declares this action ID."
                ),
            )

        # Duplicate action IDs are rejected within a definition. Across
        # definitions we resolve deterministically by capability ID.
        definition = sorted(
            matches,
            key=lambda item: item.capability_id,
        )[0]
        return self.resolve(definition.capability_id)

    def snapshot(self) -> dict[str, Any]:
        """Return resolver diagnostics for every registered capability."""
        items = [
            self.resolve(capability_id).as_dict()
            for capability_id
            in self._capability_registry.capability_ids()
        ]

        resolved = sum(
            int(bool(item["resolved"]))
            for item in items
        )
        available = sum(
            int(bool(item["available"]))
            for item in items
        )
        healthy = sum(
            int(bool(item["healthy"]))
            for item in items
        )

        return {
            "api_version": "1.0",
            "resolver_version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "capabilities": len(items),
                "resolved": resolved,
                "available": available,
                "healthy": healthy,
                "unresolved": len(items) - resolved,
                "all_resolved": resolved == len(items),
                "all_available": available == len(items),
                "all_healthy": healthy == len(items),
                "manager_enabled": True,
                "execution_migration_enabled": True,
            },
            "capabilities": items,
        }

    def _resolve_provider_binding(
        self,
        provider_capability_id: str,
    ) -> ProviderBindingResolution:
        resolution = self._provider_registry.resolution(
            provider_capability_id
        )
        provider = self._provider_registry.resolve_provider(
            provider_capability_id
        )

        if provider is None:
            return ProviderBindingResolution(
                provider_capability_id=provider_capability_id,
                resolved=False,
                selected_provider_id=None,
                candidate_provider_ids=tuple(
                    resolution.candidate_provider_ids
                ),
                loaded=None,
                available=None,
                healthy=None,
                priority=None,
                reason=resolution.reason,
            )

        runtime = provider.runtime_state()

        return ProviderBindingResolution(
            provider_capability_id=provider_capability_id,
            resolved=True,
            selected_provider_id=provider.provider_id,
            candidate_provider_ids=tuple(
                resolution.candidate_provider_ids
            ),
            loaded=runtime.loaded,
            available=runtime.available,
            healthy=runtime.healthy,
            priority=int(provider.priority),
            reason=resolution.reason,
        )
