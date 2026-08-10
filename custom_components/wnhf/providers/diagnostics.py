"""Unified provider diagnostics model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .base import WNHFProvider
from .registry import WNHFProviderRegistry


@dataclass(frozen=True, slots=True)
class ProviderDiagnosticsContext:
    """Cross-subsystem context for one provider."""

    selected_capabilities: tuple[str, ...]
    candidate_capabilities: tuple[str, ...]
    discovery: dict[str, Any] | None
    qualification: dict[str, Any] | None


class UnifiedProviderDiagnostics:
    """Build one complete self-description snapshot per provider."""

    API_VERSION = "1.0"
    VERSION = "1.0-stage4.5.4"

    def __init__(
        self,
        registry: WNHFProviderRegistry,
    ) -> None:
        self._registry = registry

    def snapshot(
        self,
        *,
        discovery_snapshot: dict[str, Any] | None,
        qualification_snapshot: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Return the complete provider diagnostic view."""
        providers = self._registry.providers()

        discovery_by_provider = {
            item.get("provider_id"): item
            for item in (
                discovery_snapshot.get("providers", [])
                if discovery_snapshot
                else []
            )
        }
        qualification_by_provider = {
            item.get("provider_id"): item
            for item in (
                qualification_snapshot.get("providers", [])
                if qualification_snapshot
                else []
            )
        }

        provider_items: list[dict[str, Any]] = []
        healthy_count = 0
        available_count = 0
        valid_count = 0
        selected_count = 0
        warning_count = 0
        error_count = 0

        for provider in providers:
            context = self._context_for(
                provider,
                discovery_by_provider.get(provider.provider_id),
                qualification_by_provider.get(provider.provider_id),
            )
            item = self._provider_snapshot(provider, context)
            provider_items.append(item)

            runtime = item["runtime"]
            contract = item["contract"]
            diagnostics = item["diagnostics"]

            healthy_count += int(bool(runtime["healthy"]))
            available_count += int(bool(runtime["available"]))
            valid_count += int(bool(contract["valid"]))
            selected_count += int(bool(item["registry"]["selected"]))
            warning_count += len(diagnostics["warnings"])
            error_count += len(diagnostics["errors"])

        status = (
            "error"
            if error_count
            else "warning"
            if warning_count
            else "healthy"
        )

        return {
            "api_version": self.API_VERSION,
            "diagnostics_version": self.VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
            "status": status,
            "summary": {
                "providers": len(provider_items),
                "healthy": healthy_count,
                "available": available_count,
                "contract_valid": valid_count,
                "selected": selected_count,
                "warnings": warning_count,
                "errors": error_count,
                "all_healthy": healthy_count == len(provider_items),
                "all_available": available_count == len(provider_items),
                "all_contracts_valid": valid_count == len(provider_items),
            },
            "providers": provider_items,
        }

    def _context_for(
        self,
        provider: WNHFProvider,
        discovery: dict[str, Any] | None,
        qualification: dict[str, Any] | None,
    ) -> ProviderDiagnosticsContext:
        selected: list[str] = []
        candidates: list[str] = []

        for capability_id in provider.supported_capabilities():
            provider_ids = tuple(
                candidate.provider_id
                for candidate in self._registry.providers_for_capability(
                    capability_id
                )
            )
            if provider.provider_id in provider_ids:
                candidates.append(capability_id)

            selected_provider = self._registry.resolve_provider(
                capability_id
            )
            if (
                selected_provider is not None
                and selected_provider.provider_id
                == provider.provider_id
            ):
                selected.append(capability_id)

        return ProviderDiagnosticsContext(
            selected_capabilities=tuple(sorted(selected)),
            candidate_capabilities=tuple(sorted(candidates)),
            discovery=discovery,
            qualification=qualification,
        )

    def _provider_snapshot(
        self,
        provider: WNHFProvider,
        context: ProviderDiagnosticsContext,
    ) -> dict[str, Any]:
        metadata = provider.metadata().as_dict()
        runtime = provider.runtime_state().as_dict()
        contract = provider.diagnostics().as_dict()["contract"]

        capability_items: list[dict[str, Any]] = []
        for capability_id in provider.supported_capabilities():
            resolution = self._registry.resolution(capability_id)
            capability_items.append({
                "capability_id": capability_id,
                "selected": (
                    resolution.selected_provider_id
                    == provider.provider_id
                ),
                "candidate_provider_ids": list(
                    resolution.candidate_provider_ids
                ),
                "resolution_reason": resolution.reason,
            })

        qualification = context.qualification
        confidence = (
            qualification.get("confidence")
            if qualification is not None
            else None
        )

        warnings: list[str] = []
        errors: list[str] = []
        recommendations: list[str] = []

        if not contract["valid"]:
            errors.extend(contract["errors"])
            recommendations.append(
                "Correct provider contract violations before selection."
            )

        if not runtime["loaded"]:
            errors.append("Provider is not loaded.")
            recommendations.append(
                "Reload the integration or inspect provider setup."
            )
        elif not runtime["healthy"]:
            warnings.append("Provider runtime is degraded.")
            recommendations.append(
                "Inspect runtime details and last_error."
            )

        if not runtime["available"]:
            warnings.append("Provider is currently unavailable.")
            recommendations.append(
                "Check provider dependencies and command entities."
            )

        if not context.selected_capabilities:
            warnings.append(
                "Provider is not selected for any declared capability."
            )
            recommendations.append(
                "Inspect priority, health and competing providers."
            )

        if context.discovery is None:
            warnings.append(
                "No discovery record exists for this provider."
            )

        if qualification is None:
            recommendations.append(
                "No provider qualification profile is currently linked."
            )

        status = (
            "error"
            if errors
            else "warning"
            if warnings
            else "healthy"
        )

        return {
            "provider_id": provider.provider_id,
            "identity": {
                "id": metadata["provider_id"],
                "version": metadata["provider_version"],
                "name": metadata["name"],
                "class_name": metadata["class_name"],
                "module": metadata["module"],
                "kind": metadata["kind"],
            },
            "runtime": runtime,
            "contract": {
                "version": metadata["contract_version"],
                "valid": contract["valid"],
                "errors": contract["errors"],
            },
            "registry": {
                "registered": self._registry.contains(
                    provider.provider_id
                ),
                "revision": self._registry.revision,
                "priority": metadata["priority"],
                "discoverable": metadata["discoverable"],
                "selected": bool(
                    context.selected_capabilities
                ),
                "selected_capabilities": list(
                    context.selected_capabilities
                ),
                "candidate_capabilities": list(
                    context.candidate_capabilities
                ),
            },
            "discovery": context.discovery,
            "qualification": qualification,
            "confidence": confidence,
            "capabilities": capability_items,
            "diagnostics": {
                "status": status,
                "warnings": warnings,
                "errors": errors,
                "recommendations": recommendations,
                "runtime_validated": runtime[
                    "runtime_validated"
                ],
                "last_error": runtime["last_error"],
            },
        }
