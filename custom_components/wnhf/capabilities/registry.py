"""Semantic capability registry."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .base import (
    CapabilityContractError,
    CapabilityDefinition,
    validate_capability_definition,
)


@dataclass(frozen=True, slots=True)
class CapabilityRegistration:
    """One capability registration result."""

    capability_id: str
    registered: bool
    enabled: bool
    provider_capability_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable registration result."""
        return {
            "capability_id": self.capability_id,
            "registered": self.registered,
            "enabled": self.enabled,
            "provider_capability_ids": list(
                self.provider_capability_ids
            ),
        }


class CapabilityRegistry:
    """Registry of semantic capability definitions."""

    VERSION = "1.0-stage4.6.1"

    def __init__(self) -> None:
        self._definitions: dict[str, CapabilityDefinition] = {}
        self._revision = 0

    @property
    def revision(self) -> int:
        """Return registry mutation revision."""
        return self._revision

    def register(
        self,
        definition: CapabilityDefinition,
    ) -> None:
        """Register one unique contract-valid capability."""
        errors = validate_capability_definition(definition)
        if errors:
            raise CapabilityContractError(
                f"Capability {definition.capability_id!r} "
                "violates contract: "
                + "; ".join(errors)
            )

        if definition.capability_id in self._definitions:
            raise ValueError(
                "Capability already registered: "
                f"{definition.capability_id}"
            )

        self._definitions[
            definition.capability_id
        ] = definition
        self._revision += 1

    def replace(
        self,
        definition: CapabilityDefinition,
    ) -> None:
        """Replace one capability by stable ID."""
        if definition.capability_id in self._definitions:
            self.unregister(definition.capability_id)
        self.register(definition)

    def unregister(
        self,
        capability_id: str,
    ) -> CapabilityDefinition | None:
        """Remove one capability."""
        definition = self._definitions.pop(
            capability_id,
            None,
        )
        if definition is not None:
            self._revision += 1
        return definition

    def get(
        self,
        capability_id: str,
    ) -> CapabilityDefinition | None:
        """Return one capability by stable ID."""
        return self._definitions.get(capability_id)

    def contains(self, capability_id: str) -> bool:
        """Return whether a capability is registered."""
        return capability_id in self._definitions

    def definitions(self) -> tuple[CapabilityDefinition, ...]:
        """Return definitions in stable ID order."""
        return tuple(
            self._definitions[key]
            for key in sorted(self._definitions)
        )

    def capability_ids(self) -> tuple[str, ...]:
        """Return all registered capability IDs."""
        return tuple(sorted(self._definitions))

    def diagnostics(
        self,
        *,
        provider_registry: Any,
    ) -> dict[str, Any]:
        """Return contract and provider-binding diagnostics."""
        definitions = self.definitions()
        items: list[dict[str, Any]] = []
        valid_count = 0
        available_count = 0
        warning_count = 0
        error_count = 0

        for definition in definitions:
            errors = validate_capability_definition(definition)
            if not errors:
                valid_count += 1

            provider_bindings: list[dict[str, Any]] = []
            all_required_available = True

            for provider_capability_id in (
                definition.required_provider_capabilities
            ):
                resolution = provider_registry.resolution(
                    provider_capability_id
                )
                provider_bindings.append(
                    resolution.as_dict()
                )
                if not resolution.resolved:
                    all_required_available = False

            warnings: list[str] = []
            item_errors = list(errors)

            if not definition.enabled:
                warnings.append(
                    "Capability is intentionally disabled."
                )

            if not all_required_available:
                item_errors.append(
                    "At least one required provider capability "
                    "cannot be resolved."
                )

            if warnings:
                warning_count += len(warnings)
            if item_errors:
                error_count += len(item_errors)

            available = (
                definition.enabled
                and not item_errors
                and all_required_available
            )
            if available:
                available_count += 1

            items.append({
                "definition": definition.as_dict(),
                "state": {
                    "registered": True,
                    "available": available,
                    "contract_valid": not errors,
                    "provider_bindings_resolved": (
                        all_required_available
                    ),
                },
                "provider_bindings": provider_bindings,
                "diagnostics": {
                    "status": (
                        "error"
                        if item_errors
                        else "warning"
                        if warnings
                        else "healthy"
                    ),
                    "warnings": warnings,
                    "errors": item_errors,
                },
            })

        return {
            "api_version": "1.0",
            "registry_version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "revision": self.revision,
            "summary": {
                "capabilities": len(definitions),
                "contract_valid": valid_count,
                "available": available_count,
                "warnings": warning_count,
                "errors": error_count,
                "all_contracts_valid": (
                    valid_count == len(definitions)
                ),
                "all_available": (
                    available_count == len(definitions)
                ),
                "resolver_enabled": True,
                "manager_enabled": True,
                "execution_migration_enabled": True,
            },
            "capability_ids": list(self.capability_ids()),
            "capabilities": items,
        }
